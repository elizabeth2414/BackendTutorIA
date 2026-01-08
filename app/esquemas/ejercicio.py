from pydantic import BaseModel
from typing import List, Optional


# ------------------------------------------------------------
# SCHEMAS PARA FRAGMENTOS
# ------------------------------------------------------------

class FragmentoPracticaBase(BaseModel):
    texto_fragmento: str
    posicion_inicio: Optional[int] = None
    posicion_fin: Optional[int] = None
    tipo_error_asociado: Optional[str] = None


class FragmentoPracticaCreate(FragmentoPracticaBase):
    ejercicio_id: int


class FragmentoPracticaResponse(FragmentoPracticaBase):
    id: int
    completado: bool
    mejora_lograda: bool

    class Config:
        orm_mode = True


# ------------------------------------------------------------
# SCHEMAS PARA EJERCICIO DE PRÁCTICA
# ------------------------------------------------------------

class EjercicioPracticaBase(BaseModel):
    tipo_ejercicio: str
    palabras_objetivo: List[str]
    texto_practica: Optional[str] = None
    dificultad: Optional[int] = 1


class EjercicioPracticaCreate(EjercicioPracticaBase):
    estudiante_id: int
    evaluacion_id: int


class EjercicioPracticaUpdate(BaseModel):
    completado: Optional[bool] = None
    dificultad: Optional[int] = None


class EjercicioPracticaResponse(EjercicioPracticaBase):
    id: int
    completado: bool
    estudiante_id: int
    evaluacion_id: int

    class Config:
        orm_mode = True


# ------------------------------------------------------------
# SCHEMAS PARA RESULTADOS DE EJERCICIOS
# ------------------------------------------------------------

class ResultadoEjercicioBase(BaseModel):
    ejercicio_id: int
    logro: Optional[str] = None


class ResultadoEjercicioCreate(ResultadoEjercicioBase):
    pass


class ResultadoEjercicioResponse(ResultadoEjercicioBase):
    id: int

    class Config:
        orm_mode = True
