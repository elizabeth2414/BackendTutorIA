from pydantic import BaseModel, EmailStr, validator
from typing import Optional, List
from datetime import datetime




class LoginRequest(BaseModel):
    """Esquema para solicitud de login"""
    email: EmailStr
    password: str




class Token(BaseModel):
    """Token de acceso JWT - ACTUALIZADO con verificación"""
    access_token: str
    token_type: str
    expires_in: int
    email_verificado: bool  
    requiere_verificacion: bool = False  


class TokenData(BaseModel):
    """Datos decodificados del token JWT"""
    usuario_id: int
    email: str
    roles: List[str]




class UsuarioBase(BaseModel):
    """Esquema base de usuario"""
    email: EmailStr
    nombre: str
    apellido: str
    activo: Optional[bool] = True


class UsuarioCreate(UsuarioBase):
    """Esquema para crear usuario - CON VALIDACIONES"""
    password: str
    
    @validator('nombre', 'apellido')
    def validar_nombre(cls, v):
        """Valida que nombre y apellido sean válidos"""
        if len(v.strip()) < 2:
            raise ValueError('Debe tener al menos 2 caracteres')
        if not v.replace(' ', '').isalpha():
            raise ValueError('Solo se permiten letras')
        return v.strip()
    
    @validator('password')
    def validar_password(cls, v):
        """Valida que la contraseña sea segura"""
        if len(v) < 6:
            raise ValueError('La contraseña debe tener al menos 6 caracteres')
        return v


class UsuarioUpdate(BaseModel):
    """Esquema para actualizar usuario"""
    email: Optional[EmailStr] = None
    nombre: Optional[str] = None
    apellido: Optional[str] = None
    activo: Optional[bool] = None


class UsuarioResponse(UsuarioBase):
    """Respuesta de usuario - ACTUALIZADO con verificación"""
    id: int
    email_verificado: bool 
    bloqueado: bool = False
    fecha_creacion: datetime
    ultimo_login: Optional[datetime] = None
    roles_nombres: List[str] = [] 

    class Config:
        from_attributes = True  

class UsuarioRolBase(BaseModel):
    """Esquema base de rol de usuario"""
    rol: str
    activo: bool = True
    fecha_expiracion: Optional[datetime] = None


class UsuarioRolCreate(UsuarioRolBase):
    """Esquema para crear asignación de rol"""
    usuario_id: int


class UsuarioRolResponse(UsuarioRolBase):
    """Respuesta de rol de usuario"""
    id: int
    usuario_id: int
    fecha_asignacion: datetime

    class Config:
        from_attributes = True




class CambioPassword(BaseModel):
    """Esquema para cambiar contraseña (usuario autenticado)"""
    password_actual: str
    password_nueva: str
    
    @validator('password_nueva')
    def validar_password_nueva(cls, v):
        """Valida que la nueva contraseña sea segura"""
        if len(v) < 6:
            raise ValueError('La contraseña debe tener al menos 6 caracteres')
        return v




class ReenviarVerificacion(BaseModel):
    """Esquema para reenviar email de verificación"""
    email: EmailStr


class VerificarEmail(BaseModel):
    """Esquema para verificar email con token"""
    token: str




class ResetPasswordRequest(BaseModel):
    """Solicitud de reset de contraseña"""
    email: EmailStr


class ResetPasswordConfirm(BaseModel):
    """Confirmación de reset de contraseña con token"""
    token: str
    nuevo_password: str
    
    @validator('nuevo_password')
    def validar_password(cls, v):
        """Valida que la nueva contraseña sea segura"""
        if len(v) < 6:
            raise ValueError('La contraseña debe tener al menos 6 caracteres')
        return v




class MensajeRespuesta(BaseModel):
    """Respuesta genérica con mensaje de éxito o error"""
    mensaje: str
    success: bool = True


class VerificacionRespuesta(BaseModel):
    """Respuesta específica de verificación de email"""
    mensaje: str
    email: str
    token: Optional[str] = None  