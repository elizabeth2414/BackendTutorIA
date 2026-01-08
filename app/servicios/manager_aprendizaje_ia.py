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
        Genera feedback personalizado y detallado para el niño.
        Incluye mensaje de voz y texto con análisis de errores.
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
        
        # 🎤 MENSAJE DE VOZ (corto y motivador)
        if mejoro:
            if precision >= 95:
                mensaje_voz = "¡Excelente trabajo! Leíste casi perfecto. ¡Eres increíble!"
                emoji = "🌟"
            elif precision >= 85:
                mensaje_voz = "¡Muy bien! Has mejorado mucho. Sigue así campeón."
                emoji = "🎉"
            else:
                mensaje_voz = "¡Bien hecho! Ya vas mejorando. Sigamos practicando juntos."
                emoji = "👏"
        else:
            if intentos == 1:
                mensaje_voz = "Buen primer intento. Vamos a practicar un poquito más."
                emoji = "💪"
            elif intentos == 2:
                mensaje_voz = "Ya casi lo tienes. Intenta leer más despacio y claro."
                emoji = "🎯"
            else:
                mensaje_voz = "No te preocupes, todos aprendemos diferente. Tómate tu tiempo."
                emoji = "🌈"
        
        # 📝 MENSAJE DETALLADO (para mostrar en pantalla)
        mensaje_detallado = self._construir_mensaje_detallado(
            precision,
            total_errores,
            omisiones,
            sustituciones,
            inserciones,
            mejoro,
        )
        
        # 🎯 PALABRAS ESPECÍFICAS CON PROBLEMAS
        palabras_problema = []
        for error in errores[:5]:  # Máximo 5 palabras
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
        """Construye mensaje detallado con análisis de errores."""
        
        if mejoro and precision >= 90:
            return (
                f"¡Felicitaciones! Tu lectura fue excelente con {precision:.0f}% de precisión. "
                f"Casi no tuviste errores. ¡Sigue así!"
            )
        
        if mejoro:
            return (
                f"¡Muy bien! Alcanzaste {precision:.0f}% de precisión. "
                f"Has mejorado mucho en este ejercicio."
            )
        
        # Mensaje cuando NO mejoró
        partes = [f"Tuviste {total} {'error' if total == 1 else 'errores'} en total:"]
        
        if omisiones > 0:
            partes.append(
                f"• {omisiones} palabra{'s' if omisiones > 1 else ''} que saltaste"
            )
        
        if sustituciones > 0:
            partes.append(
                f"• {sustituciones} palabra{'s' if sustituciones > 1 else ''} que leíste diferente"
            )
        
        if inserciones > 0:
            partes.append(
                f"• {inserciones} palabra{'s' if inserciones > 1 else ''} que agregaste"
            )
        
        partes.append("\n💡 Consejo: Lee más despacio y marca bien cada palabra.")
        
        return " ".join(partes)
    
    def _generar_sugerencia(self, error: Dict) -> str:
        """Genera sugerencia específica para cada tipo de error."""
        
        tipo = error.get("tipo_error", "")
        palabra = error.get("palabra_original", "")
        
        if tipo == "omision":
            return f"No te saltes '{palabra}'. Léela completa."
        elif tipo == "sustitucion":
            leida = error.get("palabra_leida", "")
            return f"Dijiste '{leida}' pero dice '{palabra}'."
        elif tipo == "insercion":
            return "Agregaste una palabra que no está en el texto."
        else:
            return "Revisa esta parte del texto."
    
    def _calcular_nivel_logro(self, precision: float, mejoro: bool) -> str:
        """Calcula el nivel de logro alcanzado."""
        
        if precision >= 95:
            return "excelente"
        elif precision >= 85:
            return "muy_bueno"
        elif precision >= 70:
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
        El niño practica un ejercicio concreto con feedback de voz detallado.
        """
        logger.info(
            f"🎯 Iniciando práctica | estudiante={estudiante_id} | "
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

            # 2. Analizar audio
            logger.info(f"🎤 Analizando audio | path={audio_path}")
            
            analisis = self.analizador.analizar_practica_ejercicio(
                texto_practica=ejercicio.texto_practica,
                audio_path=audio_path,
            )
            
            logger.info(
                f"📊 Análisis completado | "
                f"precisión={analisis.get('precision_global', 0):.1f}%"
            )

            # 3. Evaluar mejora
            precision = analisis.get("precision_global", 0.0)
            errores = analisis.get("errores_detectados", [])
            
            # Criterios de mejora más detallados
            if precision >= 85:
                mejoro = True
            elif precision >= 70 and len(errores) <= 2:
                mejoro = True
            elif precision >= 60 and len(errores) == 0:
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

            # 5. 🎤 GENERAR FEEDBACK DETALLADO CON VOZ
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