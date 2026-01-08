from pydantic import BaseModel
from typing import Optional, Dict, Any
from datetime import datetime

from app.esquemas.docente import DocenteResponse


class CursoBase(BaseModel):
    nombre: str
    descripcion: Optional[str] = None
    nivel: int
    codigo_acceso: Optional[str] = None
    activo: bool = True
    configuracion: Optional[Dict[str, Any]] = None


class CursoCreate(CursoBase):
    docente_id: Optional[int] = None


class CursoUpdate(BaseModel):
    nombre: Optional[str] = None
    descripcion: Optional[str] = None
    nivel: Optional[int] = None
    codigo_acceso: Optional[str] = None
    activo: Optional[bool] = None
    configuracion: Optional[Dict[str, Any]] = None


class CursoResponse(CursoBase):
    id: int
    docente_id: int
    fecha_creacion: datetime
    docente: Optional[DocenteResponse] = None

    class Config:
        from_attributes = True
