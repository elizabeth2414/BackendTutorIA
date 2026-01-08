from pydantic import BaseModel
from typing import Dict, Any, List, Optional
from datetime import date, datetime

class EstadisticasEstudiante(BaseModel):
    estudiante_id: int
    nivel_actual: int
    puntos_totales: int
    lecturas_completadas: int
    actividades_completadas: int
    racha_actual: int
    racha_maxima: int
    progreso_nivel: float
    recompensas_obtenidas: int

class ProgresoCurso(BaseModel):
    curso_id: int
    curso_nombre: str
    total_estudiantes: int
    nivel_promedio: float
    total_lecturas: int
    progreso_promedio: float

class ReporteEvaluacion(BaseModel):
    evaluacion_id: int
    fecha_evaluacion: datetime
    puntuacion_pronunciacion: float
    velocidad_lectura: float
    fluidez: float
    precision_palabras: float
    palabras_por_minuto: float

class TendenciaProgreso(BaseModel):
    fecha: date
    puntuacion_promedio: float
    lecturas_completadas: int
    actividades_completadas: int

class DashboardDocente(BaseModel):
    total_estudiantes: int
    total_cursos: int
    total_lecturas: int
    total_evaluaciones: int
    estudiantes_activos: int
    progreso_promedio: float
    tendencia_progreso: List[TendenciaProgreso]