from pydantic import BaseModel
from typing import Optional, Dict, Any
from datetime import date, datetime

from app.esquemas.usuario import UsuarioResponse
from app.esquemas.docente import DocenteResponse


class EstudianteBase(BaseModel):
    nombre: str
    apellido: str
    fecha_nacimiento: date
    nivel_educativo: int
    necesidades_especiales: Optional[str] = None
    avatar_url: Optional[str] = None
    configuracion: Optional[Dict[str, Any]] = None
    transferible: bool = True


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
    nivel_educativo: int
    necesidades_especiales: Optional[str] = None
    curso_id: int

class EstudianteUpdateDocente(BaseModel):
    nombre: Optional[str] = None
    apellido: Optional[str] = None
    fecha_nacimiento: Optional[date] = None
    nivel_educativo: Optional[int] = None
    necesidades_especiales: Optional[str] = None
    curso_id: Optional[int] = None