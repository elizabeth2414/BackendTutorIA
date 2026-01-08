from typing import List, Dict, Set
from collections import defaultdict

from sqlalchemy.orm import Session

from app.modelos import (
    EjercicioPractica,
    FragmentoPractica,
    Estudiante,
    ErrorPronunciacion,
    DetalleEvaluacion,
    EvaluacionLectura
)
from app.logs.logger import logger


class GeneradorEjercicios:
    def __init__(self) -> None:
        self.mapa_tipo_a_ejercicio = {
            "sustitucion": "palabras_aisladas",
            "omision": "oraciones",
            "insercion": "palabras_aisladas",
            "puntuacion": "puntuacion",
        }

    def _extraer_palabras_por_tipo(
        self, errores: List[Dict]
    ) -> Dict[str, Set[str]]:
        resultado: Dict[str, Set[str]] = defaultdict(set)
        for e in errores:
            tipo = e.get("tipo_error", "otro")
            if tipo not in self.mapa_tipo_a_ejercicio:
                continue
            palabra = e.get("palabra_original") or e.get("palabra_leida")
            if not palabra:
                continue
            resultado[tipo].add(palabra)
        return resultado

    def crear_ejercicios_desde_errores(
        self,
        db: Session,
        estudiante_id: int,
        evaluacion_id: int,
        errores: List[Dict],
    ) -> List[int]:
        estudiante = db.query(Estudiante).filter(Estudiante.id == estudiante_id).first()
        if not estudiante:
            return []

        palabras_por_tipo = self._extraer_palabras_por_tipo(errores)
        ejercicios_ids: List[int] = []

        for tipo_error, palabras_set in palabras_por_tipo.items():
            if not palabras_set:
                continue

            tipo_ejercicio = self.mapa_tipo_a_ejercicio.get(
                tipo_error, "palabras_aisladas"
            )
            palabras_objetivo = list(palabras_set)

            if tipo_error == "puntuacion":
                texto_practica = (
                    "Lee en voz alta las oraciones poniendo especial atención a los puntos y comas."
                )
                dificultad = 2
            elif tipo_error in ("sustitucion", "insercion"):
                texto_practica = (
                    "Repite las palabras indicadas hasta que suenen claras y correctas."
                )
                dificultad = 1
            elif tipo_error == "omision":
                texto_practica = (
                    "Lee nuevamente las oraciones completas, sin saltarte palabras."
                )
                dificultad = 2
            else:
                texto_practica = "Practica las partes indicadas de la lectura."
                dificultad = 1

            ejercicio = EjercicioPractica(
                estudiante_id=estudiante_id,
                evaluacion_id=evaluacion_id,
                tipo_ejercicio=tipo_ejercicio,
                palabras_objetivo=palabras_objetivo,
                texto_practica=texto_practica,
                dificultad=dificultad,
                completado=False,
                intentos=0,
            )
            db.add(ejercicio)
            db.flush()

            ejercicios_ids.append(ejercicio.id)

            for palabra in palabras_objetivo:
                frag_text = f"Lee en voz alta la palabra: {palabra}"
                fragmento = FragmentoPractica(
                    ejercicio_id=ejercicio.id,
                    texto_fragmento=frag_text,
                    posicion_inicio=0,
                    posicion_fin=len(frag_text),
                    tipo_error_asociado=tipo_error,
                    completado=False,
                    mejora_lograda=False,
                )
                db.add(fragmento)

        db.commit()
        return ejercicios_ids

    def crear_ejercicios_desde_bd(
        self,
        db: Session,
        evaluacion_id: int
    ) -> List[int]:
        """
        Crea ejercicios consultando los errores directamente desde la BD.

        Ventajas sobre crear_ejercicios_desde_errores:
        - No requiere pasar los errores como parámetro
        - Usa los datos ya persistidos en BD
        - Permite crear ejercicios después de la evaluación
        - Puede regenerar ejercicios si se necesita

        Args:
            db: Sesión de base de datos
            evaluacion_id: ID de la evaluación

        Returns:
            Lista de IDs de ejercicios creados
        """
        # Obtener la evaluación para verificar que existe y obtener estudiante_id
        evaluacion = db.query(EvaluacionLectura).filter(
            EvaluacionLectura.id == evaluacion_id
        ).first()

        if not evaluacion:
            logger.warning(
                f"Evaluación {evaluacion_id} no encontrada, "
                f"no se pueden crear ejercicios"
            )
            return []

        # Consultar errores desde la BD
        errores_bd = db.query(ErrorPronunciacion).join(
            DetalleEvaluacion,
            ErrorPronunciacion.detalle_evaluacion_id == DetalleEvaluacion.id
        ).filter(
            DetalleEvaluacion.evaluacion_id == evaluacion_id
        ).all()

        if not errores_bd:
            logger.info(
                f"No hay errores guardados para evaluación {evaluacion_id}, "
                f"no se crean ejercicios"
            )
            return []

        # Convertir errores de BD a formato Dict para reusar lógica existente
        errores_dict = [
            {
                "tipo_error": error.tipo_error,
                "palabra_original": error.palabra_original,
                "palabra_leida": error.palabra_detectada,
                "severidad": error.severidad
            }
            for error in errores_bd
        ]

        logger.info(
            f"📚 Creando ejercicios desde {len(errores_dict)} errores guardados "
            f"en BD para evaluación {evaluacion_id}"
        )

        # Reusar la lógica existente de crear_ejercicios_desde_errores
        ejercicios_ids = self.crear_ejercicios_desde_errores(
            db=db,
            estudiante_id=evaluacion.estudiante_id,
            evaluacion_id=evaluacion_id,
            errores=errores_dict
        )

        logger.info(
            f"✅ {len(ejercicios_ids)} ejercicios creados desde BD "
            f"para evaluación {evaluacion_id}"
        )

        return ejercicios_ids
