from pydantic import BaseModel, EmailStr, field_validator
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

    @field_validator("nombre", "apellido")
    @classmethod
    def _validar_nombres(cls, v: str):
        from app.validaciones.regex import validar_solo_letras
        return validar_solo_letras(v, min_len=2)

    @field_validator("password")
    @classmethod
    def _validar_password(cls, v: str):
        # ⚠️ Contraseñas NO deben restringirse a solo letras/números.
        # Se valida longitud mínima.
        if v is None or len(v) < 6:
            raise ValueError("La contraseña debe tener al menos 6 caracteres")
        return v

class UsuarioUpdate(BaseModel):
    email: Optional[EmailStr] = None
    nombre: Optional[str] = None
    apellido: Optional[str] = None
    activo: Optional[bool] = None

    @field_validator("nombre", "apellido")
    @classmethod
    def _validar_nombres_opt(cls, v: str | None):
        if v is None:
            return v
        from app.validaciones.regex import validar_solo_letras
        return validar_solo_letras(v, min_len=2)

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

    @field_validator("nuevo_password")
    @classmethod
    def _validar_nuevo_password(cls, v: str):
        if v is None or len(v) < 6:
            raise ValueError("La nueva contraseña debe tener al menos 6 caracteres")
        return v

class ResetPasswordRequest(BaseModel):
    email: EmailStr

class ResetPasswordConfirm(BaseModel):
    token: str
    nuevo_password: str

    @field_validator("nuevo_password")
    @classmethod
    def _validar_reset_password(cls, v: str):
        if v is None or len(v) < 6:
            raise ValueError("La nueva contraseña debe tener al menos 6 caracteres")
        return v

class ConfigurarCuentaRequest(BaseModel):
    token: str
    nuevo_password: str
