from jose import JWTError, jwt
from datetime import datetime, timedelta
from fastapi import HTTPException, status, Depends
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from typing import Optional

from app import settings
from app.config import get_db
from app.modelos import Usuario, UsuarioRol

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

def crear_token_acceso(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Crear token JWT de acceso"""
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire, "iat": datetime.utcnow()})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt

def verificar_token_acceso(token: str) -> Optional[dict]:
    """Verificar y decodificar token JWT"""
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return payload
    except JWTError:
        return None

async def obtener_usuario_actual(
    token: str = Depends(oauth2_scheme), 
    db: Session = Depends(get_db)
) -> Usuario:
    """Obtener usuario actual desde el token"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="No se pudieron validar las credenciales",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    payload = verificar_token_acceso(token)
    if payload is None:
        raise credentials_exception
    
    email: str = payload.get("sub")
    usuario_id: int = payload.get("id")
    
    if email is None or usuario_id is None:
        raise credentials_exception
    
    usuario = db.query(Usuario).filter(Usuario.id == usuario_id, Usuario.email == email).first()
    if usuario is None:
        raise credentials_exception
    
    if not usuario.activo:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Usuario inactivo"
        )
    
    return usuario

def crear_token_actualizacion(usuario_id: int) -> str:
    """Crear token de actualización"""
    data = {"sub": "refresh", "user_id": usuario_id}
    expires = timedelta(days=30)  # Token de refresco válido por 30 días
    return crear_token_acceso(data, expires)

def verificar_token_actualizacion(token: str) -> Optional[int]:
    """Verificar token de actualización"""
    payload = verificar_token_acceso(token)
    if payload and payload.get("sub") == "refresh":
        return payload.get("user_id")
    return None