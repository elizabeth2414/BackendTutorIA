# app/esquemas/padre_hijos.py
from typing import List
from pydantic import BaseModel

from app.esquemas.estudiante import EstudianteResponse
from app.esquemas.curso import CursoResponse


class EstudianteConCursosResponse(BaseModel):
    estudiante: EstudianteResponse
    cursos: List[CursoResponse]

    class Config:
        from_attributes = True
