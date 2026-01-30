from __future__ import annotations  

from pydantic import BaseModel, EmailStr, field_validator
from typing import Optional
from datetime import date, datetime

from app.esquemas.usuario import UsuarioResponse




class DocenteBase(BaseModel):
    especialidad: Optional[str] = None
    grado_academico: Optional[str] = None
    institucion: Optional[str] = None
    fecha_contratacion: Optional[date] = None
    activo: bool = True


class DocenteCreate(DocenteBase):
    
    usuario_id: int


class DocenteUpdate(BaseModel):
    # Campos del USUARIO
    nombre: Optional[str] = None
    apellido: Optional[str] = None
    email: Optional[EmailStr] = None
    
    # Campos del DOCENTE
    especialidad: Optional[str] = None
    grado_academico: Optional[str] = None
    institucion: Optional[str] = None
    fecha_contratacion: Optional[date] = None
    activo: Optional[bool] = None

    @field_validator("nombre", "apellido")
    @classmethod
    def _validar_nombre_apellido(cls, v: str | None):
        if v is None:
            return v
        from app.validaciones.regex import validar_solo_letras
        return validar_solo_letras(v, min_len=2)

    @field_validator("especialidad", "grado_academico", "institucion")
    @classmethod
    def _validar_texto_docente(cls, v: str | None):
        if v is None:
            return v
        from app.validaciones.regex import validar_alfanum_espacio
        # texto corto (sin símbolos)
        return validar_alfanum_espacio(v, min_len=2)


class DocenteResponse(DocenteBase):
    id: int
    usuario_id: int
    creado_en: datetime
    usuario: Optional[UsuarioResponse] = None

    class Config:
        from_attributes = True




class DocenteCreateAdmin(DocenteBase):
    """
    Lo que el ADMIN envía para crear un docente:
    - crea USUARIO + ROL + DOCENTE
    """
    # Datos de usuario
    email: EmailStr
    password: Optional[str] = None  # ✅ Ahora es opcional
    nombre: str
    apellido: str

    @field_validator("nombre", "apellido")
    @classmethod
    def _validar_nombre_apellido_admin(cls, v: str):
        from app.validaciones.regex import validar_solo_letras
        return validar_solo_letras(v, min_len=2)

    @field_validator("especialidad", "grado_academico", "institucion")
    @classmethod
    def _validar_texto_docente_admin(cls, v: str | None):
        if v is None:
            return v
        from app.validaciones.regex import validar_alfanum_espacio
        return validar_alfanum_espacio(v, min_len=2)


class DocenteAdminResponse(DocenteBase):
    """
    Lo que el backend devuelve al ADMIN al crear/listar docentes.
    Incluye info del usuario asociada.
    """
    id: int
    creado_en: datetime
    usuario: UsuarioResponse

    class Config:
        from_attributes = True
