from __future__ import annotations  # opcional, pero ayuda con tipos adelantados

from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import date, datetime

from app.esquemas.usuario import UsuarioResponse


# ===============================
# ESQUEMAS EXISTENTES (DOCENTE)
# ===============================

class DocenteBase(BaseModel):
    especialidad: Optional[str] = None
    grado_academico: Optional[str] = None
    institucion: Optional[str] = None
    fecha_contratacion: Optional[date] = None
    activo: bool = True


class DocenteCreate(DocenteBase):
    # Este se usa cuando YA existe el usuario y solo se crea el docente
    usuario_id: int


class DocenteUpdate(BaseModel):
    especialidad: Optional[str] = None
    grado_academico: Optional[str] = None
    institucion: Optional[str] = None
    fecha_contratacion: Optional[date] = None
    activo: Optional[bool] = None


class DocenteResponse(DocenteBase):
    id: int
    usuario_id: int
    creado_en: datetime
    usuario: Optional[UsuarioResponse] = None

    class Config:
        from_attributes = True


# ===============================
# ESQUEMAS ESPECIALES PARA ADMIN
# ===============================

class DocenteCreateAdmin(DocenteBase):
    """
    Lo que el ADMIN envía para crear un docente:
    - crea USUARIO + ROL + DOCENTE
    """
    # Datos de usuario
    email: EmailStr
    password: str
    nombre: str
    apellido: str


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
