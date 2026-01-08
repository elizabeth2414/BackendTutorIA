from pydantic import BaseModel
from typing import Optional, Dict, Any
from datetime import datetime

class AuditoriaBase(BaseModel):
    accion: str
    tabla_afectada: Optional[str] = None
    registro_id: Optional[int] = None
    datos_anteriores: Optional[Dict[str, Any]] = None
    datos_nuevos: Optional[Dict[str, Any]] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None

class AuditoriaResponse(AuditoriaBase):
    id: int
    usuario_id: Optional[int]
    fecha_evento: datetime
    
    class Config:
        from_attributes = True

class SesionUsuarioBase(BaseModel):
    token_sesion: str
    fecha_expiracion: datetime
    ip_address: Optional[str] = None
    dispositivo: Optional[str] = None
    activa: bool = True

class SesionUsuarioCreate(SesionUsuarioBase):
    usuario_id: int

class SesionUsuarioResponse(SesionUsuarioBase):
    id: int
    usuario_id: int
    fecha_inicio: datetime
    
    class Config:
        from_attributes = True