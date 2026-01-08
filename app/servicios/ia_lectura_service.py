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
        logger.info(f"Cargando modelo Faster-Whisper '{modelo}' (modo niños)...")
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
        return SequenceMatcher(None, a, b).ratio()

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

    # ================= COMPARACIÓN =================
    def _comparar_textos(
        self,
        texto_referencia: str,
        texto_leido: str,
        duracion_segundos: float,
    ) -> Dict:

        ref_tokens = self._tokenizar(texto_referencia)
        leido_tokens = self._limpiar_repeticiones(
            self._tokenizar(texto_leido)
        )

        matcher = SequenceMatcher(a=ref_tokens, b=leido_tokens)
        errores_detectados = []
        tokens_correctos = 0

        for tag, i1, i2, j1, j2 in matcher.get_opcodes():
            if tag == "equal":
                tokens_correctos += (i2 - i1)
                continue

            for i in range(i1, i2):
                palabra_original = ref_tokens[i] if i < len(ref_tokens) else None
                palabra_leida = leido_tokens[j1] if j1 < len(leido_tokens) else None

                if self._es_puntuacion(palabra_original or ""):
                    continue

                if tag == "replace":
                    if self._similitud_palabra(palabra_original, palabra_leida) >= 0.75:
                        tokens_correctos += 1
                        continue
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
                        "severidad": 2,
                    }
                )

        total = max(1, len(ref_tokens))
        precision = (tokens_correctos / total) * 100

        errores_reales = [
            e for e in errores_detectados
            if e["tipo_error"] != "puntuacion"
        ]

        # 🎯 MODO NIÑOS
        if precision >= 88 and len(errores_reales) <= 2:
            precision = 100
        elif precision >= 80:
            precision = min(100, precision + 10)

        precision = max(60, min(precision, 100))

        palabras = len([t for t in leido_tokens if not self._es_puntuacion(t)])
        ppm = (palabras / (duracion_segundos / 60)) if duracion_segundos else 0

        return {
            "precision_global": precision,
            "palabras_por_minuto": ppm,
            "errores_detectados": errores_detectados,
            "tokens_leidos": leido_tokens,
        }

    # ================= FEEDBACK =================
    def _generar_feedback(self, analisis: Dict) -> str:
        p = analisis.get("precision_global", 0)

        if p >= 95:
            return "¡Excelente! Leíste muy bien 🎉"
        if p >= 85:
            return "¡Muy bien! Cada vez lees mejor 👏"
        if p >= 70:
            return "Buen intento, vamos a practicar un poco más 💪"
        return "Lo hiciste con valentía. Practicando mejorarás 🌟"

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

        Esta función persiste:
        - Un DetalleEvaluacion por cada error detectado (palabra con problema)
        - Un ErrorPronunciacion por cada error, asociado a su detalle

        Args:
            db: Sesión de base de datos
            evaluacion_id: ID de la evaluación recién creada
            tokens_leidos: Lista de tokens que el estudiante leyó
            errores_detectados: Lista de errores detectados por el análisis
        """
        if not errores_detectados:
            logger.info(
                f"📊 No hay errores que guardar para evaluación {evaluacion_id}"
            )
            return

        total_detalles = 0
        total_errores = 0

        # Para cada error, crear un DetalleEvaluacion y un ErrorPronunciacion
        for error in errores_detectados:
            palabra_original = error.get("palabra_original")
            palabra_leida = error.get("palabra_leida")
            posicion = error.get("posicion", 0)
            tipo_error = error.get("tipo_error", "otro")
            severidad = error.get("severidad", 2)

            # Calcular precisión de la palabra (0 si hay error)
            if palabra_original and palabra_leida:
                precision_palabra = self._similitud_palabra(
                    palabra_original, palabra_leida
                ) * 100
            else:
                precision_palabra = 0.0

            # Crear DetalleEvaluacion para esta palabra
            detalle = DetalleEvaluacion(
                evaluacion_id=evaluacion_id,
                palabra=palabra_original or palabra_leida or "?",
                posicion_en_texto=posicion,
                precision_pronunciacion=precision_palabra,
                retroalimentacion_palabra=(
                    f"Error de {tipo_error}: "
                    f"esperado '{palabra_original}', "
                    f"leído '{palabra_leida}'"
                ),
                tipo_tokenizacion="word"
            )

            db.add(detalle)
            db.flush()  # Obtener el ID del detalle
            total_detalles += 1

            # Crear ErrorPronunciacion asociado a este detalle
            error_pronunciacion = ErrorPronunciacion(
                detalle_evaluacion_id=detalle.id,
                tipo_error=tipo_error,
                palabra_original=palabra_original,
                palabra_detectada=palabra_leida,
                severidad=severidad,
                sugerencia_correccion=(
                    f"Practica pronunciar la palabra '{palabra_original}' "
                    f"correctamente. Escucha el audio de referencia."
                )
            )

            db.add(error_pronunciacion)
            total_errores += 1

        # Commit de todos los detalles y errores
        db.commit()

        logger.info(
            f"💾 Guardados {total_detalles} detalles de evaluación y "
            f"{total_errores} errores de pronunciación para "
            f"evaluación {evaluacion_id}"
        )

    # ================= PRÁCTICA DE EJERCICIOS =================
    def analizar_practica_ejercicio(
        self,
        texto_practica: str,
        audio_path: str,
    ) -> Dict:
        """
        Analiza un ejercicio de práctica específico.
        No guarda en BD, solo retorna el análisis.
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