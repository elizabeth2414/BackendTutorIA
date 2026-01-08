from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime
from pydantic import BaseModel
from typing import List, Optional


class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str
    expires_in: int

class TokenData(BaseModel):
    usuario_id: int
    email: str
    roles: List[str]

class UsuarioBase(BaseModel):
    email: EmailStr
    nombre: str
    apellido: str
    activo: Optional[bool] = True

class UsuarioCreate(UsuarioBase):
    password: str

class UsuarioUpdate(BaseModel):
    email: Optional[EmailStr] = None
    nombre: Optional[str] = None
    apellido: Optional[str] = None
    activo: Optional[bool] = None

class UsuarioResponse(UsuarioBase):
    id: int
    fecha_creacion: datetime
    ultimo_login: Optional[datetime] = None
    bloqueado: bool = False
    roles: List[str] = []

    class Config:
        from_attributes = True

class UsuarioRolBase(BaseModel):
    rol: str
    activo: bool = True
    fecha_expiracion: Optional[datetime] = None

class UsuarioRolCreate(UsuarioRolBase):
    usuario_id: int

class UsuarioRolResponse(UsuarioRolBase):
    id: int
    usuario_id: int
    fecha_asignacion: datetime
    
    class Config:
        from_attributes = True

class CambioPassword(BaseModel):
    password_actual: str
    nuevo_password: str

class ResetPasswordRequest(BaseModel):
    email: EmailStr

class ResetPasswordConfirm(BaseModel):
    token: str
    nuevo_password: str