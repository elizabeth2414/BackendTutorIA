from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime

# IMPORTS NECESARIOS PARA EVITAR EL ERROR
from app.esquemas.curso import CursoResponse
from app.esquemas.docente import DocenteResponse


class CategoriaLecturaBase(BaseModel):
    nombre: str
    descripcion: Optional[str] = None
    edad_minima: int
    edad_maxima: int
    color: str = '#3498db'
    icono: Optional[str] = None
    activo: bool = True


class CategoriaLecturaCreate(CategoriaLecturaBase):
    pass


class CategoriaLecturaUpdate(BaseModel):
    nombre: Optional[str] = None
    descripcion: Optional[str] = None
    edad_minima: Optional[int] = None
    edad_maxima: Optional[int] = None
    color: Optional[str] = None
    icono: Optional[str] = None
    activo: Optional[bool] = None


class CategoriaLecturaResponse(CategoriaLecturaBase):
    id: int
    creado_en: datetime

    class Config:
        from_attributes = True


class ContenidoLecturaBase(BaseModel):
    titulo: str
    contenido: str
    audio_url: Optional[str] = None
    duracion_audio: Optional[int] = None
    nivel_dificultad: int
    edad_recomendada: int
    palabras_clave: Optional[List[str]] = None
    etiquetas: Optional[Dict[str, Any]] = None
    por_defecto: bool = False
    publico: bool = False
    activo: bool = True


class ContenidoLecturaCreate(ContenidoLecturaBase):
    curso_id: Optional[int] = None
    docente_id: Optional[int] = None
    categoria_id: Optional[int] = None


class ContenidoLecturaUpdate(BaseModel):
    titulo: Optional[str] = None
    contenido: Optional[str] = None
    audio_url: Optional[str] = None
    duracion_audio: Optional[int] = None
    nivel_dificultad: Optional[int] = None
    edad_recomendada: Optional[int] = None
    palabras_clave: Optional[List[str]] = None
    etiquetas: Optional[Dict[str, Any]] = None
    por_defecto: Optional[bool] = None
    publico: Optional[bool] = None
    activo: Optional[bool] = None


class ContenidoLecturaResponse(ContenidoLecturaBase):
    id: int
    curso_id: Optional[int]
    docente_id: Optional[int]
    categoria_id: Optional[int]
    fecha_creacion: datetime
    fecha_actualizacion: datetime

    # ✔ YA NO EN STRING
    curso: Optional[CursoResponse] = None
    docente: Optional[DocenteResponse] = None
    categoria: Optional[CategoriaLecturaResponse] = None

    class Config:
        from_attributes = True


class AudioReferenciaBase(BaseModel):
    audio_url: str
    duracion: int
    tipo: Optional[str] = None
    transcripcion: Optional[str] = None


class AudioReferenciaCreate(AudioReferenciaBase):
    contenido_id: int


class AudioReferenciaResponse(AudioReferenciaBase):
    id: int
    contenido_id: int
    fecha_creacion: datetime

    class Config:
        from_attributes = True
