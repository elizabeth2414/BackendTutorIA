from pydantic import BaseModel, Field, field_validator
from typing import Optional, Dict, Any
from datetime import date, datetime

from app.esquemas.usuario import UsuarioResponse
from app.esquemas.docente import DocenteResponse


class EstudianteBase(BaseModel):
    nombre: str
    apellido: str
    fecha_nacimiento: date
    nivel_educativo: int = Field(..., ge=1, le=12)
    necesidades_especiales: Optional[str] = None
    avatar_url: Optional[str] = None
    configuracion: Optional[Dict[str, Any]] = None
    transferible: bool = True

    @field_validator("nombre", "apellido")
    @classmethod
    def _validar_nombre_apellido_base(cls, v: str):
        from app.validaciones.regex import validar_solo_letras
        return validar_solo_letras(v, min_len=2)

    @field_validator("necesidades_especiales")
    @classmethod
    def _validar_necesidades_base(cls, v: str | None):
        if v is None:
            return v
        from app.validaciones.regex import validar_texto_libre
        return validar_texto_libre(v, max_len=200)


class EstudianteCreate(EstudianteBase):
    docente_id: int
    usuario_id: Optional[int] = None


class EstudianteUpdate(BaseModel):
    fecha_nacimiento: Optional[date] = None
    nivel_educativo: Optional[int] = None
    necesidades_especiales: Optional[str] = None
    avatar_url: Optional[str] = None
    configuracion: Optional[Dict[str, Any]] = None
    activo: Optional[bool] = None
    transferible: Optional[bool] = None

    @field_validator("nivel_educativo")
    @classmethod
    def _validar_nivel_update(cls, v: int | None):
        if v is None:
            return v
        if v < 1 or v > 12:
            raise ValueError("Nivel educativo inválido")
        return v

    @field_validator("necesidades_especiales")
    @classmethod
    def _validar_necesidades_update(cls, v: str | None):
        if v is None:
            return v
        from app.validaciones.regex import validar_texto_libre
        return validar_texto_libre(v, max_len=200)


class EstudianteResponse(EstudianteBase):
    id: int
    usuario_id: Optional[int]
    docente_id: int
    creado_en: datetime
    activo: bool

    usuario: Optional[UsuarioResponse] = None
    docente: Optional[DocenteResponse] = None

    class Config:
        from_attributes = True


class NivelEstudianteBase(BaseModel):
    nivel_actual: int = 1
    puntos_totales: int = 0
    puntos_nivel_actual: int = 0
    puntos_para_siguiente_nivel: int = 1000
    lecturas_completadas: int = 0
    actividades_completadas: int = 0
    racha_actual: int = 0
    racha_maxima: int = 0


class NivelEstudianteResponse(NivelEstudianteBase):
    id: int
    estudiante_id: int
    fecha_actualizacion: datetime

    class Config:
        from_attributes = True


class EstudianteCreateDocente(BaseModel):
    nombre: str
    apellido: str
    fecha_nacimiento: date
    nivel_educativo: int = Field(..., ge=1, le=12)
    necesidades_especiales: Optional[str] = None
    curso_id: int = Field(..., ge=1)

    @field_validator("nombre", "apellido")
    @classmethod
    def _validar_nombres_create_docente(cls, v: str):
        from app.validaciones.regex import validar_solo_letras
        return validar_solo_letras(v, min_len=2)

    @field_validator("necesidades_especiales")
    @classmethod
    def _validar_necesidades_create_docente(cls, v: str | None):
        if v is None:
            return v
        from app.validaciones.regex import validar_texto_libre
        return validar_texto_libre(v, max_len=200)

class EstudianteUpdateDocente(BaseModel):
    nombre: Optional[str] = None
    apellido: Optional[str] = None
    fecha_nacimiento: Optional[date] = None
    nivel_educativo: Optional[int] = None
    necesidades_especiales: Optional[str] = None
    curso_id: Optional[int] = Field(None, ge=1)

    @field_validator("nombre", "apellido")
    @classmethod
    def _validar_nombres(cls, v: str | None):
        if v is None:
            return v
        from app.validaciones.regex import validar_solo_letras
        return validar_solo_letras(v, min_len=2)

    @field_validator("necesidades_especiales")
    @classmethod
    def _validar_necesidades(cls, v: str | None):
        if v is None:
            return v
        from app.validaciones.regex import validar_texto_libre
        # texto corto, sin símbolos peligrosos
        return validar_texto_libre(v, max_len=200)