# app/esquemas/estudiante_curso.py

from pydantic import BaseModel
from typing import Literal
from datetime import datetime


class EstudianteCursoBase(BaseModel):
    estado: Literal["activo", "inactivo", "suspendido"] = "activo"


class EstudianteCursoCreate(EstudianteCursoBase):
    estudiante_id: int
    curso_id: int


class EstudianteCursoResponse(EstudianteCursoBase):
    id: int
    estudiante_id: int
    curso_id: int
    fecha_inscripcion: datetime

    class Config:
        from_attributes = True
