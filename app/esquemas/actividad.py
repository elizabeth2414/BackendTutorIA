from pydantic import BaseModel
from typing import List, Optional


# ------------------------------------------------------------
# SCHEMAS PARA ACTIVIDADES
# ------------------------------------------------------------

class ActividadBase(BaseModel):
    titulo: str
    descripcion: Optional[str] = None
    tipo: str   # lectura, practica, cuestionario, etc.
    nivel: Optional[int] = None
    categoria_id: Optional[int] = None


class ActividadCreate(ActividadBase):
    docente_id: int


class ActividadUpdate(BaseModel):
    titulo: Optional[str] = None
    descripcion: Optional[str] = None
    tipo: Optional[str] = None
    nivel: Optional[int] = None
    categoria_id: Optional[int] = None


class ActividadResponse(ActividadBase):
    id: int
    docente_id: int

    class Config:
        from_attributes = True


# ------------------------------------------------------------
# SCHEMAS PARA PREGUNTAS DE ACTIVIDAD
# ------------------------------------------------------------

class PreguntaBase(BaseModel):
    actividad_id: int
    pregunta: str
    respuesta_correcta: str


class PreguntaCreate(PreguntaBase):
    pass


class PreguntaResponse(PreguntaBase):
    id: int

    class Config:
        from_attributes = True


# ------------------------------------------------------------
# PROGRESO DE ACTIVIDAD POR ESTUDIANTE
# ------------------------------------------------------------

class ProgresoActividadBase(BaseModel):
    actividad_id: int
    estudiante_id: int
    estado: Optional[str] = None  # iniciado, completado
    puntaje: Optional[int] = None


class ProgresoActividadCreate(ProgresoActividadBase):
    pass


class ProgresoActividadResponse(ProgresoActividadBase):
    id: int

    class Config:
        from_attributes = True


# ------------------------------------------------------------
# RESPUESTA DE PREGUNTAS
# ------------------------------------------------------------

class RespuestaPreguntaBase(BaseModel):
    pregunta_id: int
    estudiante_id: int
    respuesta: str


class RespuestaPreguntaCreate(RespuestaPreguntaBase):
    pass


class RespuestaPreguntaResponse(RespuestaPreguntaBase):
    id: int
    correcta: Optional[bool] = None

    class Config:
        from_attributes = True
