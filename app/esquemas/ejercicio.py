from __future__ import annotations

from pydantic import BaseModel, Field, field_validator
from typing import List, Optional


class FragmentoPracticaBase(BaseModel):
    texto_fragmento: str = Field(..., min_length=1, max_length=500)
    posicion_inicio: Optional[int] = Field(default=None, ge=0)
    posicion_fin: Optional[int] = Field(default=None, ge=0)
    tipo_error_asociado: Optional[str] = None

    @field_validator("tipo_error_asociado")
    @classmethod
    def _validar_tipo_error(cls, v: str | None):
        if v is None:
            return v
        from app.validaciones.regex import validar_alfanum_espacio
        return validar_alfanum_espacio(v, min_len=2)


class FragmentoPracticaCreate(FragmentoPracticaBase):
    ejercicio_id: int = Field(..., ge=1)


class FragmentoPracticaResponse(FragmentoPracticaBase):
    id: int
    completado: bool
    mejora_lograda: bool

    class Config:
        from_attributes = True


class EjercicioPracticaBase(BaseModel):
    tipo_ejercicio: str
    palabras_objetivo: List[str]
    texto_practica: Optional[str] = None
    dificultad: Optional[int] = Field(default=1, ge=1, le=10)

    @field_validator("tipo_ejercicio")
    @classmethod
    def _validar_tipo_ejercicio(cls, v: str):
        from app.validaciones.regex import validar_alfanum_espacio
        return validar_alfanum_espacio(v, min_len=2)

    @field_validator("palabras_objetivo")
    @classmethod
    def _validar_palabras_objetivo(cls, v: List[str]):
        from app.validaciones.regex import validar_solo_letras
        return [validar_solo_letras(p, min_len=1) for p in v]

    @field_validator("texto_practica")
    @classmethod
    def _validar_texto_practica(cls, v: str | None):
        if v is None:
            return v
        from app.validaciones.regex import validar_texto_libre
        return validar_texto_libre(v, max_len=10000)


class EjercicioPracticaCreate(EjercicioPracticaBase):
    estudiante_id: int = Field(..., ge=1)
    evaluacion_id: int = Field(..., ge=1)


class EjercicioPracticaUpdate(BaseModel):
    completado: Optional[bool] = None
    dificultad: Optional[int] = Field(default=None, ge=1, le=10)


class EjercicioPracticaResponse(EjercicioPracticaBase):
    id: int
    completado: bool
    estudiante_id: int
    evaluacion_id: int

    class Config:
        from_attributes = True


class ResultadoEjercicioBase(BaseModel):
    ejercicio_id: int = Field(..., ge=1)
    logro: Optional[str] = None

    @field_validator("logro")
    @classmethod
    def _validar_logro(cls, v: str | None):
        if v is None:
            return v
        from app.validaciones.regex import validar_texto_libre
        return validar_texto_libre(v, max_len=500)


class ResultadoEjercicioCreate(ResultadoEjercicioBase):
    pass


class ResultadoEjercicioResponse(ResultadoEjercicioBase):
    id: int

    class Config:
        from_attributes = True
