from pydantic import BaseModel
from typing import Optional
from datetime import datetime, date

class RecompensaBase(BaseModel):
    nombre: str
    descripcion: Optional[str] = None
    tipo: str
    puntos_requeridos: Optional[int] = None
    nivel_requerido: Optional[int] = None
    lectura_id: Optional[int] = None
    imagen_url: Optional[str] = None
    rareza: str = 'comun'
    activo: bool = True

class RecompensaCreate(RecompensaBase):
    pass

class RecompensaResponse(RecompensaBase):
    id: int
    fecha_creacion: datetime
    
    class Config:
        from_attributes = True

class RecompensaEstudianteBase(BaseModel):
    visto: bool = False

class RecompensaEstudianteCreate(RecompensaEstudianteBase):
    estudiante_id: int
    recompensa_id: int

class RecompensaEstudianteResponse(RecompensaEstudianteBase):
    id: int
    estudiante_id: int
    recompensa_id: int
    fecha_obtencion: datetime
    recompensa: Optional['RecompensaResponse'] = None
    
    class Config:
        from_attributes = True

class MisionDiariaBase(BaseModel):
    tipo_mision: Optional[str] = None
    objetivo: Optional[int] = None
    progreso: int = 0
    completada: bool = False
    recompensa_puntos: int = 50

class MisionDiariaCreate(MisionDiariaBase):
    estudiante_id: int

class MisionDiariaResponse(MisionDiariaBase):
    id: int
    estudiante_id: int
    fecha: date
    
    class Config:
        from_attributes = True

class HistorialPuntosBase(BaseModel):
    motivo: Optional[str] = None
    puntos: Optional[int] = None

class HistorialPuntosCreate(HistorialPuntosBase):
    estudiante_id: int

class HistorialPuntosResponse(HistorialPuntosBase):
    id: int
    estudiante_id: int
    fecha: datetime
    
    class Config:
        from_attributes = True