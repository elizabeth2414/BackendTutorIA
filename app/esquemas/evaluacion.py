from pydantic import BaseModel
from typing import Optional, Dict, Any
from datetime import datetime

# IMPORTS NECESARIOS
from app.esquemas.estudiante import EstudianteResponse
from app.esquemas.contenido import ContenidoLecturaResponse


class EvaluacionLecturaBase(BaseModel):
    puntuacion_pronunciacion: Optional[float] = None
    velocidad_lectura: Optional[float] = None
    fluidez: Optional[float] = None
    precision_palabras: Optional[float] = None
    retroalimentacion_ia: Optional[str] = None
    audio_url: Optional[str] = None
    duracion_audio: Optional[int] = None
    estado: str = 'completado'


class EvaluacionLecturaCreate(EvaluacionLecturaBase):
    estudiante_id: int
    contenido_id: int


class EvaluacionLecturaResponse(EvaluacionLecturaBase):
    id: int
    estudiante_id: int
    contenido_id: int
    fecha_evaluacion: datetime

    # QUITAR STRINGS
    estudiante: Optional[EstudianteResponse] = None
    contenido: Optional[ContenidoLecturaResponse] = None

    class Config:
        from_attributes = True


class AnalisisIABase(BaseModel):
    modelo_usado: Optional[str] = None
    precision_global: Optional[float] = None
    palabras_detectadas: Optional[Dict[str, Any]] = None
    errores_detectados: Optional[Dict[str, Any]] = None
    tiempo_procesamiento: Optional[float] = None
    palabras_por_minuto: Optional[float] = None
    pausas_detectadas: Optional[Dict[str, Any]] = None
    entonacion_score: Optional[float] = None
    ritmo_score: Optional[float] = None


class AnalisisIACreate(AnalisisIABase):
    evaluacion_id: int


class AnalisisIAResponse(AnalisisIABase):
    id: int
    evaluacion_id: int
    fecha_analisis: datetime

    class Config:
        from_attributes = True


class IntentoLecturaBase(BaseModel):
    numero_intento: int
    puntuacion_pronunciacion: Optional[float] = None
    velocidad_lectura: Optional[float] = None
    fluidez: Optional[float] = None
    audio_url: Optional[str] = None


class IntentoLecturaCreate(IntentoLecturaBase):
    evaluacion_id: int


class IntentoLecturaResponse(IntentoLecturaBase):
    id: int
    evaluacion_id: int
    fecha_intento: datetime

    class Config:
        from_attributes = True


class DetalleEvaluacionBase(BaseModel):
    palabra: str
    posicion_en_texto: int
    precision_pronunciacion: Optional[float] = None
    retroalimentacion_palabra: Optional[str] = None
    timestamp_inicio: Optional[float] = None
    timestamp_fin: Optional[float] = None
    tipo_tokenizacion: Optional[str] = None


class DetalleEvaluacionCreate(DetalleEvaluacionBase):
    evaluacion_id: int


class DetalleEvaluacionResponse(DetalleEvaluacionBase):
    id: int
    evaluacion_id: int

    class Config:
        from_attributes = True


class ErrorPronunciacionBase(BaseModel):
    tipo_error: str
    palabra_original: Optional[str] = None
    palabra_detectada: Optional[str] = None
    timestamp_inicio: Optional[float] = None
    timestamp_fin: Optional[float] = None
    severidad: Optional[int] = None
    sugerencia_correccion: Optional[str] = None


class ErrorPronunciacionCreate(ErrorPronunciacionBase):
    detalle_evaluacion_id: int


class ErrorPronunciacionResponse(ErrorPronunciacionBase):
    id: int
    detalle_evaluacion_id: int

    class Config:
        from_attributes = True
