# app/esquemas/actividad_lectura.py

from typing import Optional, Any
from datetime import datetime
from pydantic import BaseModel, Field


class ActividadLecturaBase(BaseModel):
    """Esquema base para actividades de lectura"""
    tipo: str = Field(..., description="Tipo de actividad (comprension, vocabulario, etc.)")
    enunciado: str = Field(..., description="Enunciado o pregunta de la actividad")
    opciones: Optional[Any] = Field(None, description="Opciones de respuesta (JSON)")
    respuesta_correcta: Optional[str] = Field(None, description="Respuesta correcta")
    explicacion: Optional[str] = Field(None, description="Explicación de la respuesta")
    edad_min: int = Field(default=7, ge=5, le=12, description="Edad mínima recomendada")
    edad_max: int = Field(default=10, ge=5, le=12, description="Edad máxima recomendada")
    dificultad: str = Field(default="media", description="Nivel de dificultad: facil, media, dificil")
    origen: str = Field(default="ia", description="Origen de la actividad: ia, docente, sistema")
    activo: bool = Field(default=True, description="Si la actividad está activa")


class ActividadLecturaCreate(ActividadLecturaBase):
    """Esquema para crear una nueva actividad de lectura"""
    lectura_id: int = Field(..., description="ID del contenido de lectura asociado")


class ActividadLecturaUpdate(BaseModel):
    """Esquema para actualizar una actividad de lectura"""
    tipo: Optional[str] = None
    enunciado: Optional[str] = None
    opciones: Optional[Any] = None
    respuesta_correcta: Optional[str] = None
    explicacion: Optional[str] = None
    edad_min: Optional[int] = Field(None, ge=5, le=12)
    edad_max: Optional[int] = Field(None, ge=5, le=12)
    dificultad: Optional[str] = None
    origen: Optional[str] = None
    activo: Optional[bool] = None


class ActividadLecturaResponse(ActividadLecturaBase):
    """Esquema de respuesta para actividades de lectura"""
    id: int
    lectura_id: int
    creado_en: datetime

    model_config = {
        "from_attributes": True
    }


class ActividadLecturaConLectura(ActividadLecturaResponse):
    """Esquema de respuesta que incluye información de la lectura"""
    lectura_titulo: Optional[str] = None
    lectura_nivel: Optional[int] = None

    model_config = {
        "from_attributes": True
    }
