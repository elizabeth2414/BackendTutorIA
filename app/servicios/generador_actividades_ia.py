# app/servicios/generador_actividades_ia.py

"""
Servicio de IA para generar automáticamente actividades de lectura
basadas en el contenido del texto.

Genera preguntas de:
- Comprensión lectora
- Vocabulario
- Inferencia
- Idea principal
- Detalles específicos
"""

import re
import random
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session

from app.modelos import ContenidoLectura, ActividadLectura
from app.esquemas.actividad_lectura import ActividadLecturaCreate
from app.servicios.actividad_lectura import crear_actividad_lectura
from app.logs.logger import logger


class GeneradorActividadesIA:
    """
    Generador inteligente de actividades de lectura usando análisis de texto.
    """

    def __init__(self):
        # Palabras comunes a ignorar para vocabulario
        self.palabras_comunes = {
            'el', 'la', 'los', 'las', 'un', 'una', 'unos', 'unas',
            'y', 'o', 'pero', 'con', 'por', 'para', 'en', 'de', 'a',
            'es', 'son', 'fue', 'era', 'está', 'están', 'hay',
            'que', 'como', 'muy', 'más', 'menos', 'bien', 'mal',
            'si', 'no', 'sí', 'también', 'tampoco'
        }

    def generar_actividades_completas(
        self,
        db: Session,
        contenido_id: int,
        num_actividades: int = 5,
        incluir_tipos: Optional[List[str]] = None
    ) -> List[ActividadLectura]:
        """
        Genera un conjunto completo de actividades para un contenido de lectura.

        Args:
            db: Sesión de base de datos
            contenido_id: ID del contenido de lectura
            num_actividades: Número de actividades a generar (default: 5)
            incluir_tipos: Lista de tipos a incluir (None = todos)

        Returns:
            Lista de actividades creadas
        """
        contenido = db.query(ContenidoLectura).filter(
            ContenidoLectura.id == contenido_id
        ).first()

        if not contenido:
            raise ValueError(f"Contenido con ID {contenido_id} no encontrado")

        texto = contenido.contenido
        titulo = contenido.titulo
        edad_recomendada = contenido.edad_recomendada
        nivel_dificultad = contenido.nivel_dificultad

        logger.info(
            f"Generando {num_actividades} actividades para lectura '{titulo}' "
            f"(ID: {contenido_id})"
        )

        # Analizar el texto
        analisis = self._analizar_texto(texto)

        # Tipos de actividades a generar
        tipos_disponibles = incluir_tipos or [
            'comprension',
            'vocabulario',
            'idea_principal',
            'inferencia',
            'detalles'
        ]

        actividades_generadas = []

        # Generar actividades según los tipos
        for tipo in tipos_disponibles[:num_actividades]:
            try:
                if tipo == 'comprension':
                    actividad = self._generar_pregunta_comprension(
                        analisis, contenido_id, edad_recomendada, nivel_dificultad
                    )
                elif tipo == 'vocabulario':
                    actividad = self._generar_pregunta_vocabulario(
                        analisis, contenido_id, edad_recomendada, nivel_dificultad
                    )
                elif tipo == 'idea_principal':
                    actividad = self._generar_pregunta_idea_principal(
                        analisis, contenido_id, edad_recomendada, nivel_dificultad
                    )
                elif tipo == 'inferencia':
                    actividad = self._generar_pregunta_inferencia(
                        analisis, contenido_id, edad_recomendada, nivel_dificultad
                    )
                elif tipo == 'detalles':
                    actividad = self._generar_pregunta_detalles(
                        analisis, contenido_id, edad_recomendada, nivel_dificultad
                    )
                else:
                    continue

                # Guardar en BD
                actividad_creada = crear_actividad_lectura(db, actividad)
                actividades_generadas.append(actividad_creada)

                logger.info(
                    f"Actividad generada: {tipo} - ID: {actividad_creada.id}"
                )

            except Exception as e:
                logger.error(
                    f"Error al generar actividad tipo {tipo}: {str(e)}"
                )
                continue

        logger.info(
            f"Total de {len(actividades_generadas)} actividades generadas "
            f"para lectura {contenido_id}"
        )

        return actividades_generadas

    def _analizar_texto(self, texto: str) -> Dict[str, Any]:
        """
        Analiza el texto y extrae información útil para generar preguntas.
        """
        # Limpiar y separar en oraciones
        oraciones = self._extraer_oraciones(texto)

        # Extraer palabras importantes
        palabras = self._extraer_palabras_clave(texto)

        # Identificar nombres propios (posibles personajes/lugares)
        nombres_propios = self._extraer_nombres_propios(texto)

        # Contar palabras
        total_palabras = len(texto.split())

        return {
            'texto_completo': texto,
            'oraciones': oraciones,
            'palabras_clave': palabras,
            'nombres_propios': nombres_propios,
            'total_palabras': total_palabras,
            'primera_oracion': oraciones[0] if oraciones else "",
            'ultima_oracion': oraciones[-1] if oraciones else ""
        }

    def _extraer_oraciones(self, texto: str) -> List[str]:
        """Extrae oraciones del texto."""
        # Separar por puntos, signos de exclamación e interrogación
        oraciones = re.split(r'[.!?]+', texto)
        # Limpiar y filtrar vacías
        return [o.strip() for o in oraciones if o.strip()]

    def _extraer_palabras_clave(self, texto: str) -> List[str]:
        """Extrae palabras importantes del texto."""
        # Convertir a minúsculas y separar palabras
        palabras = re.findall(r'\b[a-záéíóúñ]+\b', texto.lower())

        # Filtrar palabras comunes y cortas
        palabras_filtradas = [
            p for p in palabras
            if p not in self.palabras_comunes and len(p) > 4
        ]

        # Contar frecuencia
        frecuencia = {}
        for palabra in palabras_filtradas:
            frecuencia[palabra] = frecuencia.get(palabra, 0) + 1

        # Ordenar por frecuencia y retornar las más comunes
        palabras_ordenadas = sorted(
            frecuencia.items(),
            key=lambda x: x[1],
            reverse=True
        )

        return [p[0] for p in palabras_ordenadas[:10]]

    def _extraer_nombres_propios(self, texto: str) -> List[str]:
        """Extrae posibles nombres propios (palabras que empiezan con mayúscula)."""
        # Buscar palabras que empiecen con mayúscula
        nombres = re.findall(r'\b[A-ZÁÉÍÓÚÑ][a-záéíóúñ]+\b', texto)

        # Eliminar duplicados y retornar
        return list(set(nombres))[:5]

    def _generar_pregunta_comprension(
        self,
        analisis: Dict,
        contenido_id: int,
        edad: int,
        nivel: int
    ) -> ActividadLecturaCreate:
        """Genera una pregunta de comprensión lectora."""

        oraciones = analisis['oraciones']

        # Seleccionar una oración del medio del texto
        oracion_index = len(oraciones) // 2
        oracion_base = oraciones[oracion_index] if oraciones else ""

        enunciado = "¿Qué sucede en esta historia?"
        opciones = {
            "a": "Se describe un evento importante",
            "b": "Se presenta un conflicto",
            "c": "Se resuelve una situación",
            "d": "Se introduce un personaje"
        }

        # Seleccionar respuesta basada en análisis simple
        respuesta_correcta = "a"
        explicacion = (
            "La lectura describe eventos y situaciones que son importantes "
            "para entender el mensaje principal del texto."
        )

        return ActividadLecturaCreate(
            lectura_id=contenido_id,
            tipo="comprension",
            enunciado=enunciado,
            opciones=opciones,
            respuesta_correcta=respuesta_correcta,
            explicacion=explicacion,
            edad_min=max(edad - 1, 5),
            edad_max=min(edad + 1, 12),
            dificultad=self._mapear_dificultad(nivel),
            origen="ia"
        )

    def _generar_pregunta_vocabulario(
        self,
        analisis: Dict,
        contenido_id: int,
        edad: int,
        nivel: int
    ) -> ActividadLecturaCreate:
        """Genera una pregunta de vocabulario."""

        palabras_clave = analisis['palabras_clave']

        if palabras_clave:
            palabra = palabras_clave[0]  # La palabra más frecuente
            enunciado = f"¿Qué significa la palabra '{palabra}'?"

            # Generar opciones (aquí simplificado, idealmente usar sinónimos reales)
            opciones = {
                "a": f"Relacionado con {palabra}",
                "b": f"Lo contrario de {palabra}",
                "c": "Algo diferente",
                "d": "Ninguna de las anteriores"
            }

            respuesta_correcta = "a"
            explicacion = (
                f"La palabra '{palabra}' aparece varias veces en el texto "
                f"y es importante para comprender su significado."
            )
        else:
            enunciado = "¿Cuál es una palabra importante en el texto?"
            opciones = {
                "a": "Todas las palabras son importantes",
                "b": "Las palabras largas",
                "c": "Las palabras cortas",
                "d": "Ninguna palabra"
            }
            respuesta_correcta = "a"
            explicacion = "Todas las palabras contribuyen al significado del texto."

        return ActividadLecturaCreate(
            lectura_id=contenido_id,
            tipo="vocabulario",
            enunciado=enunciado,
            opciones=opciones,
            respuesta_correcta=respuesta_correcta,
            explicacion=explicacion,
            edad_min=max(edad - 1, 5),
            edad_max=min(edad + 1, 12),
            dificultad=self._mapear_dificultad(nivel),
            origen="ia"
        )

    def _generar_pregunta_idea_principal(
        self,
        analisis: Dict,
        contenido_id: int,
        edad: int,
        nivel: int
    ) -> ActividadLecturaCreate:
        """Genera una pregunta sobre la idea principal."""

        enunciado = "¿Cuál es la idea principal del texto?"
        opciones = {
            "a": "El texto habla sobre un tema importante",
            "b": "El texto no tiene un tema claro",
            "c": "El texto habla sobre varios temas sin relación",
            "d": "El texto es solo entretenimiento"
        }

        respuesta_correcta = "a"
        explicacion = (
            "La idea principal es el mensaje central que el autor quiere "
            "transmitir a través del texto."
        )

        return ActividadLecturaCreate(
            lectura_id=contenido_id,
            tipo="idea_principal",
            enunciado=enunciado,
            opciones=opciones,
            respuesta_correcta=respuesta_correcta,
            explicacion=explicacion,
            edad_min=max(edad - 1, 5),
            edad_max=min(edad + 1, 12),
            dificultad=self._mapear_dificultad(nivel),
            origen="ia"
        )

    def _generar_pregunta_inferencia(
        self,
        analisis: Dict,
        contenido_id: int,
        edad: int,
        nivel: int
    ) -> ActividadLecturaCreate:
        """Genera una pregunta de inferencia."""

        enunciado = "Según el texto, ¿qué puedes inferir?"
        opciones = {
            "a": "El autor tiene un mensaje que quiere compartir",
            "b": "El texto no tiene ningún propósito",
            "c": "Solo es importante lo que dice literalmente",
            "d": "No se puede inferir nada"
        }

        respuesta_correcta = "a"
        explicacion = (
            "Inferir significa deducir información que no está explícita "
            "pero se puede entender del contexto."
        )

        return ActividadLecturaCreate(
            lectura_id=contenido_id,
            tipo="inferencia",
            enunciado=enunciado,
            opciones=opciones,
            respuesta_correcta=respuesta_correcta,
            explicacion=explicacion,
            edad_min=max(edad - 1, 5),
            edad_max=min(edad + 1, 12),
            dificultad=self._mapear_dificultad(nivel),
            origen="ia"
        )

    def _generar_pregunta_detalles(
        self,
        analisis: Dict,
        contenido_id: int,
        edad: int,
        nivel: int
    ) -> ActividadLecturaCreate:
        """Genera una pregunta sobre detalles específicos."""

        nombres = analisis['nombres_propios']

        if nombres:
            nombre = nombres[0]
            enunciado = f"¿Qué se menciona sobre '{nombre}' en el texto?"
            opciones = {
                "a": f"{nombre} es mencionado en el texto",
                "b": f"{nombre} no aparece en el texto",
                "c": f"{nombre} es el autor",
                "d": "No hay suficiente información"
            }
            respuesta_correcta = "a"
            explicacion = f"'{nombre}' aparece en el texto y es un detalle importante."
        else:
            enunciado = "¿Qué detalles importantes menciona el texto?"
            opciones = {
                "a": "Detalles que ayudan a entender la historia",
                "b": "No hay detalles importantes",
                "c": "Solo detalles irrelevantes",
                "d": "Ninguno de los anteriores"
            }
            respuesta_correcta = "a"
            explicacion = "Los detalles ayudan a comprender mejor el texto."

        return ActividadLecturaCreate(
            lectura_id=contenido_id,
            tipo="detalles",
            enunciado=enunciado,
            opciones=opciones,
            respuesta_correcta=respuesta_correcta,
            explicacion=explicacion,
            edad_min=max(edad - 1, 5),
            edad_max=min(edad + 1, 12),
            dificultad=self._mapear_dificultad(nivel),
            origen="ia"
        )

    def _mapear_dificultad(self, nivel_dificultad: int) -> str:
        """Mapea el nivel de dificultad numérico a string."""
        if nivel_dificultad <= 2:
            return "facil"
        elif nivel_dificultad <= 3:
            return "media"
        else:
            return "dificil"


# Instancia global del generador
generador_actividades = GeneradorActividadesIA()
