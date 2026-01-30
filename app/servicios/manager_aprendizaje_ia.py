from typing import Dict, List, Optional
from sqlalchemy.orm import Session

from app.servicios.ia_lectura_service import ServicioAnalisisLectura
from app.servicios.generador_ejercicios import GeneradorEjercicios
from app.modelos import EjercicioPractica, FragmentoPractica
from app.logs.logger import logger


class ManagerAprendizajeIA:
    def __init__(self) -> None:
        self.analizador = ServicioAnalisisLectura()
        self.generador = GeneradorEjercicios()

    def procesar_lectura(
        self,
        db: Session,
        estudiante_id: int,
        contenido_id: int,
        audio_path: str,
        evaluacion_id: Optional[int] = None,
    ) -> Dict:
        resultado_analisis = self.analizador.analizar_lectura(
            db=db,
            estudiante_id=estudiante_id,
            contenido_id=contenido_id,
            audio_path=audio_path,
            evaluacion_id=evaluacion_id,
        )

        evaluacion_id_real = resultado_analisis["evaluacion_id"]
        errores = resultado_analisis.get("errores", [])

        ejercicios_ids = self.generador.crear_ejercicios_desde_errores(
            db=db,
            estudiante_id=estudiante_id,
            evaluacion_id=evaluacion_id_real,
            errores=errores,
        )

        ejercicios_info: List[Dict] = []
        if ejercicios_ids:
            ejercicios = (
                db.query(EjercicioPractica)
                .filter(EjercicioPractica.id.in_(ejercicios_ids))
                .all()
            )
            for ej in ejercicios:
                ejercicios_info.append(
                    {
                        "id": ej.id,
                        "tipo_ejercicio": ej.tipo_ejercicio,
                        "texto_practica": ej.texto_practica,
                        "palabras_objetivo": ej.palabras_objetivo,
                        "dificultad": ej.dificultad,
                        "completado": ej.completado,
                    }
                )

        resultado_analisis["ejercicios_recomendados"] = ejercicios_info
        return resultado_analisis

    def _generar_feedback_detallado(
        self,
        precision: float,
        errores: List[Dict],
        mejoro: bool,
        intentos: int,
    ) -> Dict:
        """
        Genera feedback personalizado SÚPER MOTIVADOR para niños de 7-10 años.
        Extremadamente positivo y alentador.
        """

        # 🎯 ANÁLISIS DE ERRORES POR TIPO
        errores_por_tipo = {
            "omision": [],
            "sustitucion": [],
            "insercion": [],
        }

        for error in errores:
            tipo = error.get("tipo_error", "otro")
            if tipo in errores_por_tipo:
                errores_por_tipo[tipo].append(error)

        # 📊 ESTADÍSTICAS
        total_errores = len(errores)
        omisiones = len(errores_por_tipo["omision"])
        sustituciones = len(errores_por_tipo["sustitucion"])
        inserciones = len(errores_por_tipo["insercion"])

        # 🎤 MENSAJE DE VOZ (extremadamente motivador para niños pequeños)
        if mejoro:
            if precision >= 90:
                mensajes_voz = [
                    "¡Eres un súper campeón! ¡Leíste increíble! ¡Estoy súper orgulloso de ti! 🌟",
                    "¡Guauuuu! ¡Qué maravilla de lectura! ¡Eres una estrella brillante! ✨",
                    "¡Fantástico! ¡Qué bien leíste! ¡Eres el mejor! ¡Sigue así! 🏆",
                ]
                emoji = "🌟"
            elif precision >= 75:
                mensajes_voz = [
                    "¡Muy bien hecho, campeón! ¡Mejoraste un montón! ¡Me encanta! 🎉",
                    "¡Excelente trabajo! ¡Cada día lees mejor! ¡Qué orgullo! 👏",
                    "¡Súper! ¡Tu práctica está dando resultados! ¡Eres genial! ⭐",
                ]
                emoji = "🎉"
            else:
                mensajes_voz = [
                    "¡Bien hecho! ¡Vas mejorando! ¡Sigamos practicando juntos! 💪",
                    "¡Genial! ¡Ya vas por buen camino! ¡Cada intento cuenta! 🚀",
                    "¡Qué bien! ¡Estás aprendiendo! ¡Sigue así, campeón! 🌈",
                ]
                emoji = "👏"
        else:
            if intentos == 1:
                mensajes_voz = [
                    "¡Buen primer intento, campeón! ¡Vamos a practicar juntos! 💙",
                    "¡Lo estás haciendo bien! ¡Con práctica lo lograrás! 🎈",
                    "¡Qué valiente! ¡Cada lectura te hace más fuerte! 🌻",
                ]
                emoji = "💪"
            elif intentos == 2:
                mensajes_voz = [
                    "¡Ya casi lo tienes! ¡Lee despacito y lo lograrás! ¡Tú puedes! 🎯",
                    "¡Vas mejorando! ¡Un intento más y lo tendrás! 💫",
                    "¡Sigue así! ¡Estás muy cerca de lograrlo! 🎨",
                ]
                emoji = "🎯"
            else:
                mensajes_voz = [
                    "¡Lo estás haciendo genial! ¡Cada niño aprende a su ritmo! ¡Tómate tu tiempo! 🌈",
                    "¡Sigue intentando, campeón! ¡Cada intento es un paso adelante! 🌟",
                    "¡Qué bien que no te rindes! ¡Aprender lleva tiempo y está bien! 💙",
                ]
                emoji = "🌈"

        import random
        mensaje_voz = random.choice(mensajes_voz)

        # 📝 MENSAJE DETALLADO (muy amigable y motivador)
        mensaje_detallado = self._construir_mensaje_detallado(
            precision,
            total_errores,
            omisiones,
            sustituciones,
            inserciones,
            mejoro,
        )

        # 🎯 PALABRAS ESPECÍFICAS CON PROBLEMAS (con sugerencias amigables)
        palabras_problema = []
        for error in errores[:3]:  # Solo las 3 más importantes para no abrumar
            if error.get("palabra_original"):
                palabras_problema.append({
                    "palabra": error["palabra_original"],
                    "tipo_error": error["tipo_error"],
                    "sugerencia": self._generar_sugerencia(error),
                })

        # 🏆 NIVEL DE LOGRO
        nivel_logro = self._calcular_nivel_logro(precision, mejoro)

        return {
            "mensaje_voz": mensaje_voz,
            "mensaje_detallado": mensaje_detallado,
            "emoji": emoji,
            "precision": round(precision, 1),
            "total_errores": total_errores,
            "omisiones": omisiones,
            "sustituciones": sustituciones,
            "inserciones": inserciones,
            "palabras_problema": palabras_problema,
            "nivel_logro": nivel_logro,
            "mejora_lograda": mejoro,
        }

    def _construir_mensaje_detallado(
        self,
        precision: float,
        total: int,
        omisiones: int,
        sustituciones: int,
        inserciones: int,
        mejoro: bool,
    ) -> str:
        """Construye mensaje detallado súper motivador para niños."""

        if mejoro and precision >= 85:
            return (
                f"¡Felicidades!  ¡Tu lectura fue hermosa con {precision:.0f}%! "
                f"¡Casi no tuviste errores! ¡Eres un súper lector! Sigue así. "
            )

        if mejoro:
            return (
                f"¡Muy bien!  ¡Lograste {precision:.0f}%! "
                f"¡Has mejorado muchísimo! ¡Me encanta tu esfuerzo! "
            )

        # Mensaje cuando NO mejoró (MUY positivo y motivador)
        if total == 0:
            return "¡Perfecto! ¡Leíste sin errores! ¡Eres increíble! "

        if total == 1:
            return (
                f"¡Súper bien! Solo tuviste 1 pequeñito error. "
                f"¡Casi lo tienes perfecto! Vamos a practicar esa palabrita juntos. "
            )

        if total <= 3:
            return (
                f"¡Buen trabajo! Tuviste solo {total} pequeños errores. "
                f"¡Lo estás haciendo muy bien! Vamos a mejorar juntos. "
            )

        partes = [f"Tuviste {total} pequeños errores, pero ¡lo intentaste y eso es lo que te ayudara a mejorar! "]

        if omisiones > 0:
            partes.append(
                f"Te saltaste {omisiones} palabra{'s' if omisiones > 1 else ''}. "
                f"¡Lee despacito con tu dedito! "
            )

        if sustituciones > 0:
            partes.append(
                f"Leíste {sustituciones} palabra{'s' if sustituciones > 1 else ''} diferente. "
                f"¡Ya casi las tienes! Practica diciéndolas. "
            )

        if inserciones > 0:
            partes.append(
                f"Agregaste {inserciones} palabra{'s' if inserciones > 1 else ''} de más. "
                f"¡Sigue el texto con tu dedito! "
            )

        partes.append(
            "\n Consejito de tu amigo: Lee despacito, palabra por palabra. "
            "¡No hay prisa! ¡Lo estás haciendo genial! "
        )

        return " ".join(partes)

    def _generar_sugerencia(self, error: Dict) -> str:
        """Genera sugerencia súper amigable para cada tipo de error."""

        tipo = error.get("tipo_error", "")
        palabra = error.get("palabra_original", "")

        if tipo == "omision":
            return f"Lee despacito y marca '{palabra}' con tu dedito. ¡Así no te la saltarás! "
        elif tipo == "sustitucion":
            leida = error.get("palabra_leida", "")
            return f"Dijiste '{leida}' pero es '{palabra}'. ¡Repite conmigo: '{palabra}'! "
        elif tipo == "insercion":
            return "Lee siguiendo el texto con tu dedito. ¡Eso te ayudará un montón! "
        else:
            return "Practica esta palabrita varias veces. ¡Lo harás genial! "

    def _calcular_nivel_logro(self, precision: float, mejoro: bool) -> str:
        """Calcula el nivel de logro - más generoso para niños."""

        if precision >= 90:
            return "excelente"
        elif precision >= 75:
            return "muy_bueno"
        elif precision >= 60:
            return "bueno"
        elif mejoro:
            return "mejorando"
        else:
            return "practicando"

    def practicar_ejercicio(
        self,
        db: Session,
        estudiante_id: int,
        ejercicio_id: int,
        audio_path: str,
    ) -> Dict:
        """
        El niño practica un ejercicio concreto.
        MUY TOLERANTE para niños de 7-10 años.
        """
        logger.info(
            f" Iniciando práctica | estudiante={estudiante_id} | "
            f"ejercicio={ejercicio_id}"
        )

        try:
            # 1. Buscar ejercicio
            ejercicio = (
                db.query(EjercicioPractica)
                .filter(
                    EjercicioPractica.id == ejercicio_id,
                    EjercicioPractica.estudiante_id == estudiante_id,
                )
                .first()
            )

            if not ejercicio:
                logger.error(
                    f"❌ Ejercicio no encontrado | id={ejercicio_id} | "
                    f"estudiante={estudiante_id}"
                )
                raise ValueError(
                    "Ejercicio de práctica no encontrado para este estudiante."
                )

            logger.info(
                f"✅ Ejercicio encontrado | tipo={ejercicio.tipo_ejercicio} | "
                f"texto={ejercicio.texto_practica[:50]}..."
            )

            # =========================================================
            # ✅ FIX: usar palabras_objetivo si texto_practica es instrucción
            # =========================================================
            texto_para_analizar = (ejercicio.texto_practica or "").strip()
            texto_lower = texto_para_analizar.lower()

            parece_instruccion = (
                texto_lower.startswith("repite")
                or "palabras indicadas" in texto_lower
                or "hasta que" in texto_lower
                or texto_lower.startswith("lee")
                or "pronuncia" in texto_lower
            )

            if (
                parece_instruccion
                and getattr(ejercicio, "palabras_objetivo", None)
                and len(ejercicio.palabras_objetivo or []) > 0
            ):
                palabras = [
                    (p or "").strip()
                    for p in (ejercicio.palabras_objetivo or [])
                    if (p or "").strip()
                ]
                if palabras:
                    texto_para_analizar = " ".join(palabras)

            logger.info(f"🧪 Texto usado para evaluar: {texto_para_analizar}")

            # 2. Analizar audio
            logger.info(f"🎤 Analizando audio | path={audio_path}")

            analisis = self.analizador.analizar_practica_ejercicio(
                texto_practica=texto_para_analizar,
                audio_path=audio_path,
            )

            logger.info(
                f"📊 Análisis completado | "
                f"precisión={analisis.get('precision_global', 0):.1f}%"
            )

            # 3. Evaluar mejora (MUY PERMISIVO para niños de 7-10 años)
            precision = analisis.get("precision_global", 0.0)
            errores = analisis.get("errores_detectados", [])

            # 🎯 CRITERIOS SÚPER GENEROSOS PARA NIÑOS PEQUEÑOS
            if precision >= 75:  # Bajado de 82 para ser más motivador
                mejoro = True
            elif precision >= 65 and len(errores) <= 4:  # Muy permisivo
                mejoro = True
            elif precision >= 55 and len(errores) <= 2:
                mejoro = True
            elif len(errores) == 0:  # Si no tiene errores, siempre mejoró
                mejoro = True
            else:
                mejoro = False

            logger.info(
                f"🎯 Evaluación | mejora={mejoro} | errores={len(errores)}"
            )

            # 4. Actualizar ejercicio
            ejercicio.intentos = (ejercicio.intentos or 0) + 1
            if mejoro:
                ejercicio.completado = True

                # Marcar fragmentos como mejorados
                fragmentos = (
                    db.query(FragmentoPractica)
                    .filter(FragmentoPractica.ejercicio_id == ejercicio.id)
                    .all()
                )
                for frag in fragmentos:
                    frag.completado = True
                    frag.mejora_lograda = True

            db.commit()
            db.refresh(ejercicio)

            logger.info(
                f"✅ Ejercicio actualizado | completado={ejercicio.completado} | "
                f"intentos={ejercicio.intentos}"
            )

            # 5. 🎤 GENERAR FEEDBACK SÚPER MOTIVADOR
            feedback = self._generar_feedback_detallado(
                precision=precision,
                errores=errores,
                mejoro=mejoro,
                intentos=ejercicio.intentos,
            )

            # 6. Combinar resultados
            resultado = {
                **analisis,
                **feedback,
                "ejercicio_completado": bool(ejercicio.completado),
                "ejercicio_intentos": int(ejercicio.intentos or 0),
                "ejercicio_tipo": ejercicio.tipo_ejercicio,
            }

            logger.info("🎉 Práctica de ejercicio completada exitosamente")
            return resultado

        except ValueError as ve:
            logger.error(f"❌ Error de validación: {ve}")
            raise
        except Exception as e:
            logger.exception("❌ Error inesperado en práctica de ejercicio")
            raise
