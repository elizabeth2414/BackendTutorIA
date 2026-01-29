import re
import time
import unicodedata
from typing import Dict, List, Optional

from difflib import SequenceMatcher
from sqlalchemy.orm import Session
from faster_whisper import WhisperModel

from app.logs.logger import logger
from app.modelos import (
    ContenidoLectura,
    EvaluacionLectura,
    AnalisisIA,
    DetalleEvaluacion,
    ErrorPronunciacion,
    Estudiante,
    IntentoLectura,
)


class ServicioAnalisisLectura:
    TOKEN_REGEX = r"[A-Za-zÁÉÍÓÚÜáéíóúüñÑ0-9]+|[¿\?¡!.,;:]"

    def __init__(self, modelo: str = "small") -> None:
        logger.info(f"Cargando modelo Faster-Whisper '{modelo}' (modo niños 7-10 años)...")
        self.model = WhisperModel(modelo, device="cpu", compute_type="int8")
        logger.info("Modelo Faster-Whisper cargado correctamente.")

    # ================= UTILIDADES TEXTO =================
    def _normalizar_texto(self, texto: str) -> str:
        if not texto:
            return ""
        texto = texto.replace("\n", " ").strip().lower()
        texto = unicodedata.normalize("NFD", texto)
        texto = "".join(c for c in texto if unicodedata.category(c) != "Mn")
        texto = re.sub(r"\s+", " ", texto)
        return texto

    def _tokenizar(self, texto: str) -> List[str]:
        return re.findall(
            self.TOKEN_REGEX,
            self._normalizar_texto(texto),
            flags=re.UNICODE,
        )
    def _tokenizar_con_tildes(self, texto: str) -> List[str]:
        """
        Tokeniza el texto preservando las tildes.
        Se usa para mostrar las palabras originales al usuario.
        """
        if not texto:
            return []
        # Solo normalizar espacios y convertir a minúsculas, SIN quitar tildes
        texto = texto.replace("\n", " ").strip().lower()
        texto = re.sub(r"\s+", " ", texto)
        return re.findall(
            self.TOKEN_REGEX,
            texto,
            flags=re.UNICODE,
        )

    def _es_puntuacion(self, token: str) -> bool:
        return bool(re.fullmatch(r"[¿\?¡!.,;:]", token or ""))

    def _limpiar_repeticiones(self, tokens: List[str]) -> List[str]:
        resultado = []
        for t in tokens:
            if not resultado or resultado[-1] != t:
                resultado.append(t)
        return resultado

    def _similitud_palabra(self, a: str, b: str) -> float:
        if not a or not b:
            return 0.0
        # Normalizar ambas palabras para comparación justa
        a_norm = self._normalizar_texto(a)
        b_norm = self._normalizar_texto(b)
        return SequenceMatcher(None, a_norm, b_norm).ratio()

    # ================= TRANSCRIPCIÓN =================
    def _transcribir_audio(self, audio_path: str) -> Dict:
        inicio = time.time()

        segments, info = self.model.transcribe(
            audio_path,
            language="es",
            beam_size=1,
            best_of=1,
            temperature=0.4,
            vad_filter=True,
            vad_parameters={
                "min_silence_duration_ms": 300,
                "speech_pad_ms": 200,
            },
            condition_on_previous_text=False,
        )

        texto = "".join(seg.text for seg in segments).strip()
        duracion = float(getattr(info, "duration", 0.0) or 0.0)

        logger.info(
            f"Transcripción completada | duración={duracion:.2f}s | "
            f"tiempo={time.time() - inicio:.2f}s"
        )

        return {
            "texto": texto,
            "duracion": duracion,
            "tiempo_procesamiento": time.time() - inicio,
        }

    # ================= COMPARACIÓN MÁS TOLERANTE PARA NIÑOS =================
    def _comparar_textos(
        self,
        texto_referencia: str,
        texto_leido: str,
        duracion_segundos: float,
    ) -> Dict:
        
        # 🆕 Guardar tokens CON tildes para mostrar al usuario
        ref_tokens_originales = self._tokenizar_con_tildes(texto_referencia)
        # Tokens normalizados (sin tildes) para comparación
        ref_tokens = self._tokenizar(texto_referencia)
        leido_tokens = self._limpiar_repeticiones(
            self._tokenizar(texto_leido)
        )

        matcher = SequenceMatcher(a=ref_tokens, b=leido_tokens)
        errores_detectados = []
        tokens_correctos = 0

        # 🎯 UMBRAL DE SIMILITUD MÁS PERMISIVO PARA NIÑOS
        # Para niños de 7-10 años, aceptamos mayor variación en la pronunciación
        UMBRAL_SIMILITUD_NINOS = 0.65  # Antes era 0.75

        for tag, i1, i2, j1, j2 in matcher.get_opcodes():
            if tag == "equal":
                tokens_correctos += (i2 - i1)
                continue

            for i in range(i1, i2):
                # 🆕 Palabra CON tildes para mostrar al usuario
                palabra_original = ref_tokens_originales[i] if i < len(ref_tokens_originales) else None
                # Palabra SIN tildes para comparaciones
                palabra_original_norm = ref_tokens[i] if i < len(ref_tokens) else None
                palabra_leida = leido_tokens[j1] if j1 < len(leido_tokens) else None

                # Ignorar errores de puntuación para niños
                if self._es_puntuacion(palabra_original_norm or ""):
                    continue

                if tag == "replace":
                    # Mucho más tolerante con palabras similares
                    similitud = self._similitud_palabra(palabra_original_norm, palabra_leida)
                    
                    if similitud >= UMBRAL_SIMILITUD_NINOS:
                        tokens_correctos += 1
                        continue
                    
                    # Si la palabra es MUY parecida (>= 0.5), considerarla como medio correcta
                    if similitud >= 0.5:
                        tokens_correctos += 0.7  # Dar crédito parcial
                        # Registrar como error leve
                    
                    tipo_error = "sustitucion"
                elif tag == "delete":
                    tipo_error = "omision"
                elif tag == "insert":
                    tipo_error = "insercion"
                else:
                    tipo_error = "otro"

                errores_detectados.append(
                    {
                        "tipo_error": tipo_error,
                        "palabra_original": palabra_original,
                        "palabra_leida": palabra_leida,
                        "posicion": i,
                        "severidad": 1,  # Severidad baja por defecto para niños
                    }
                )

        total = max(1, len(ref_tokens))
        precision = (tokens_correctos / total) * 100

        errores_reales = [
            e for e in errores_detectados
            if e["tipo_error"] != "puntuacion"
        ]

        # 🎯 SISTEMA DE RECOMPENSA MUY GENEROSO PARA NIÑOS DE 7-10 AÑOS
        # Los niños necesitan mucho refuerzo positivo
        
        # Si tiene muy pocos errores, considerar perfecto
        if len(errores_reales) <= 1:
            precision = 100
        elif len(errores_reales) <= 3 and precision >= 75:
            precision = 95
        elif len(errores_reales) <= 5 and precision >= 70:
            precision = 90
        # Bonificación general por esfuerzo
        elif precision >= 75:
            precision = min(100, precision + 15)
        elif precision >= 60:
            precision = min(100, precision + 20)
        elif precision >= 50:
            precision = min(100, precision + 15)
        
        # Piso mínimo de 50% para no desanimar
        precision = max(50, min(precision, 100))

        palabras = len([t for t in leido_tokens if not self._es_puntuacion(t)])
        ppm = (palabras / (duracion_segundos / 60)) if duracion_segundos > 0 else 0

        return {
            "precision_global": precision,
            "palabras_por_minuto": ppm,
            "errores_detectados": errores_detectados,
            "tokens_leidos": leido_tokens,
        }

    # ================= FEEDBACK SÚPER MOTIVADOR PARA NIÑOS =================
    def _generar_feedback(self, analisis: Dict) -> str:
        """
        Genera feedback extremadamente motivador y amigable para niños de 7-10 años.
        Usa un lenguaje muy positivo, inclusivo y alentador.
        """
        p = analisis.get("precision_global", 0)
        errores = analisis.get("errores_detectados", [])
        num_errores = len([e for e in errores if e.get("tipo_error") != "puntuacion"])

        # Feedback súper positivo y motivador - ajustado para niños
        if p >= 90:
            mensajes = [
                "¡Increíble! ¡Leíste súper bien! 🌟 Eres un campeón de la lectura.",
                "¡Guau! ¡Qué maravilla! 🎉 Leíste casi perfecto. ¡Estoy muy orgulloso!",
                "¡Fantástico trabajo! ✨ ¡Lees increíble! ¡Eres una estrella! ⭐",
                "¡Excelente! 🏆 ¡Tu lectura fue hermosa! ¡Sigue brillando así!",
            ]
        elif p >= 75:
            mensajes = [
                "¡Muy bien! 👏 ¡Leíste genial! Cada día mejoras más. ¡Sigue así!",
                "¡Genial! 🎯 ¡Qué bien lo hiciste! Tu esfuerzo se nota muchísimo.",
                "¡Súper! 🌈 ¡Me encantó cómo leíste! Estás mejorando un montón.",
                "¡Bien hecho! ⭐ ¡Qué lectura tan linda! Cada vez lees con más confianza.",
            ]
        elif p >= 60:
            mensajes = [
                "¡Buen trabajo! 💪 ¡Lo estás haciendo muy bien! Sigamos practicando juntos.",
                "¡Qué bien! 🎈 ¡Ya casi lo tienes! Con un poquito más lo harás perfecto.",
                "¡Vas súper bien! 🚀 ¡Cada intento es una victoria! ¡No te rindas!",
                "¡Bien! 🌟 ¡Me gusta cómo te esfuerzas! Sigamos practicando.",
            ]
        else:
            mensajes = [
                "¡Qué valiente eres! 💙 ¡Leíste con mucho valor! Vamos paso a paso, sin prisa.",
                "¡Lo estás intentando! 🌻 ¡Eso es lo más importante! Cada día aprendemos más.",
                "¡Bien hecho por intentarlo! 🎨 ¡Aprender es un viaje! Sigamos juntos.",
                "¡Sigue adelante! 🌈 ¡Cada lectura te hace más fuerte! ¡Tú puedes!",
            ]

        # Seleccionar mensaje basado en la precisión
        import random
        mensaje_base = random.choice(mensajes)

        # Agregar consejos específicos SOLO si tiene varios errores
        if num_errores >= 5:
            consejos = [
                " 💡 Consejito: Lee despacito, palabra por palabra. ¡No hay apuro!",
                " 💡 Consejito: Sigue las palabras con tu dedito mientras lees.",
                " 💡 Consejito: Respira hondo y lee con calma. ¡Lo estás haciendo genial!",
            ]
            mensaje_base += random.choice(consejos)
        elif num_errores >= 3:
            mensaje_base += " 💡 ¡Casi lo tienes! Practica las palabras difíciles en voz alta."

        return mensaje_base

    # ================= FLUJO PRINCIPAL =================
    def analizar_lectura(
        self,
        db: Session,
        estudiante_id: int,
        contenido_id: int,
        audio_path: str,
        evaluacion_id: Optional[int] = None,
    ) -> Dict:

        estudiante = db.get(Estudiante, estudiante_id)
        contenido = db.get(ContenidoLectura, contenido_id)

        if not estudiante or not contenido:
            raise ValueError("Estudiante o contenido no encontrado")

        trans = self._transcribir_audio(audio_path)
        analisis = self._comparar_textos(
            contenido.contenido,
            trans["texto"],
            trans["duracion"],
        )

        feedback = self._generar_feedback(analisis)

        # 1. Crear evaluación general
        evaluacion = EvaluacionLectura(
            estudiante_id=estudiante_id,
            contenido_id=contenido_id,
            puntuacion_pronunciacion=analisis["precision_global"],
            velocidad_lectura=analisis["palabras_por_minuto"],
            precision_palabras=analisis["precision_global"],
            retroalimentacion_ia=feedback,
            audio_url=audio_path,
            estado="completado",
        )

        db.add(evaluacion)
        db.commit()
        db.refresh(evaluacion)

        logger.info(
            f"✅ Evaluación creada: ID={evaluacion.id}, "
            f"Precisión={analisis['precision_global']:.1f}%"
        )

        # 2. Guardar detalles por palabra y errores de pronunciación
        self._guardar_detalles_y_errores(
            db=db,
            evaluacion_id=evaluacion.id,
            tokens_leidos=analisis.get("tokens_leidos", []),
            errores_detectados=analisis.get("errores_detectados", [])
        )

        return {
            "success": True,
            "evaluacion_id": evaluacion.id,
            "precision_global": analisis["precision_global"],
            "palabras_por_minuto": analisis["palabras_por_minuto"],
            "errores": analisis["errores_detectados"],
            "texto_transcrito": trans["texto"],
            "retroalimentacion": feedback,
        }

    def _guardar_detalles_y_errores(
        self,
        db: Session,
        evaluacion_id: int,
        tokens_leidos: List[str],
        errores_detectados: List[Dict]
    ):
        """
        Guarda DetalleEvaluacion y ErrorPronunciacion en la BD.
        """
        if not errores_detectados:
            logger.info(
                f"📊 ¡Perfecto! No hay errores para evaluación {evaluacion_id}"
            )
            return

        total_detalles = 0
        total_errores = 0

        for error in errores_detectados:
            palabra_original = error.get("palabra_original")
            palabra_leida = error.get("palabra_leida")
            posicion = error.get("posicion", 0)
            tipo_error = error.get("tipo_error", "otro")
            severidad = error.get("severidad", 1)  # Severidad baja por defecto

            if palabra_original and palabra_leida:
                precision_palabra = self._similitud_palabra(
                    palabra_original, palabra_leida
                ) * 100
            else:
                precision_palabra = 0.0

            # Mensajes super amigables para niños
            if tipo_error == "omision":
                mensaje = f"Te saltaste '{palabra_original}'. ¡No pasa nada! Lee despacito y verás todas las palabras. 💙"
            elif tipo_error == "sustitucion":
                mensaje = f"Dijiste '{palabra_leida}' pero es '{palabra_original}'. ¡Casi la tienes! Sigue intentando. 🌟"
            elif tipo_error == "insercion":
                mensaje = f"Agregaste una palabra de más. ¡Lee siguiendo con tu dedito y verás! 👆"
            else:
                mensaje = f"Pequeño errorito en '{palabra_original}'. ¡No te preocupes! Practica esta palabra. 💪"

            detalle = DetalleEvaluacion(
                evaluacion_id=evaluacion_id,
                palabra=palabra_original or palabra_leida or "?",
                posicion_en_texto=posicion,
                precision_pronunciacion=precision_palabra,
                retroalimentacion_palabra=mensaje,
                tipo_tokenizacion="word"
            )

            db.add(detalle)
            db.flush()
            total_detalles += 1

            # Sugerencias muy motivadoras
            if tipo_error == "omision":
                sugerencia = f"¡Lee despacito y marca '{palabra_original}' con tu dedito! Así no te la saltarás. 💪"
            elif tipo_error == "sustitucion":
                sugerencia = f"Di '{palabra_original}' varias veces en voz alta. ¡Repite conmigo! ⭐"
            elif tipo_error == "insercion":
                sugerencia = "Sigue las palabras del texto con tu dedo. ¡Eso te ayudará muchísimo! 👆"
            else:
                sugerencia = f"Escucha cómo suena '{palabra_original}' y repítelo despacito. 🎧"

            error_pronunciacion = ErrorPronunciacion(
                detalle_evaluacion_id=detalle.id,
                tipo_error=tipo_error,
                palabra_original=palabra_original,
                palabra_detectada=palabra_leida,
                severidad=severidad,
                sugerencia_correccion=sugerencia
            )

            db.add(error_pronunciacion)
            total_errores += 1

        db.commit()

        logger.info(
            f"💾 Guardados {total_detalles} detalles y {total_errores} errores "
            f"para evaluación {evaluacion_id}"
        )

    # ================= PRÁCTICA DE EJERCICIOS =================
    def analizar_practica_ejercicio(
        self,
        texto_practica: str,
        audio_path: str,
    ) -> Dict:
        """
        Analiza un ejercicio de práctica específico.
        Muy tolerante para niños de 7-10 años.
        """
        logger.info(f"🎯 Analizando práctica de ejercicio | audio={audio_path}")

        trans = self._transcribir_audio(audio_path)
        analisis = self._comparar_textos(
            texto_practica,
            trans["texto"],
            trans["duracion"],
        )

        logger.info(
            f"✅ Análisis de práctica completado | "
            f"precisión={analisis['precision_global']:.1f}% | "
            f"errores={len(analisis['errores_detectados'])}"
        )

        return {
            "precision_global": analisis["precision_global"],
            "palabras_por_minuto": analisis["palabras_por_minuto"],
            "errores_detectados": analisis["errores_detectados"],
            "texto_transcrito": trans["texto"],
        }