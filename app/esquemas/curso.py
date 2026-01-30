from pydantic import BaseModel, Field, field_validator
from typing import Optional, Dict, Any
from datetime import datetime

from app.esquemas.docente import DocenteResponse


class CursoBase(BaseModel):
    nombre: str
    descripcion: Optional[str] = None
    nivel: int = Field(..., ge=1, le=12)
    codigo_acceso: Optional[str] = None
    activo: bool = True
    configuracion: Optional[Dict[str, Any]] = None

    @field_validator("nombre")
    @classmethod
    def _validar_nombre(cls, v: str):
        from app.validaciones.regex import validar_alfanum_espacio
        # Permite letras/números/espacios, sin símbolos
        return validar_alfanum_espacio(v, min_len=3)

    @field_validator("descripcion")
    @classmethod
    def _validar_descripcion(cls, v: str | None):
        if v is None:
            return v
        from app.validaciones.regex import validar_texto_libre
        # Texto libre pero bloquea < > ` ; $ | \\ y símbolos raros
        return validar_texto_libre(v, max_len=500)

    @field_validator("codigo_acceso")
    @classmethod
    def _validar_codigo_acceso(cls, v: str | None):
        if v is None:
            return v
        from app.validaciones.regex import validar_codigo_acceso
        return validar_codigo_acceso(v)


class CursoCreate(CursoBase):
    docente_id: Optional[int] = None


class CursoUpdate(BaseModel):
    nombre: Optional[str] = None
    descripcion: Optional[str] = None
    nivel: Optional[int] = None
    codigo_acceso: Optional[str] = None
    activo: Optional[bool] = None
    configuracion: Optional[Dict[str, Any]] = None

    @field_validator("nombre")
    @classmethod
    def _validar_nombre_up(cls, v: str | None):
        if v is None:
            return v
        from app.validaciones.regex import validar_alfanum_espacio
        return validar_alfanum_espacio(v, min_len=3)

    @field_validator("descripcion")
    @classmethod
    def _validar_descripcion_up(cls, v: str | None):
        if v is None:
            return v
        from app.validaciones.regex import validar_texto_libre
        return validar_texto_libre(v, max_len=500)

    @field_validator("nivel")
    @classmethod
    def _validar_nivel_up(cls, v: int | None):
        if v is None:
            return v
        if v < 1 or v > 12:
            raise ValueError("Nivel inválido")
        return v

    @field_validator("codigo_acceso")
    @classmethod
    def _validar_codigo_acceso_up(cls, v: str | None):
        if v is None:
            return v
        from app.validaciones.regex import validar_codigo_acceso
        return validar_codigo_acceso(v)


class CursoResponse(CursoBase):
    id: int
    docente_id: int
    fecha_creacion: datetime
    docente: Optional[DocenteResponse] = None

    class Config:
        from_attributes = True
