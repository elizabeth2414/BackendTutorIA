from sqlalchemy.orm import Session
from fastapi import HTTPException, status
import re

from app.modelos import Usuario

def validar_email_unico(db: Session, email: str, usuario_id: int = None) -> bool:
    """Validar que el email sea único"""
    query = db.query(Usuario).filter(Usuario.email == email)
    if usuario_id:
        query = query.filter(Usuario.id != usuario_id)
    
    existe = query.first()
    if existe:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El email ya está registrado"
        )
    return True

def validar_formato_email(email: str) -> bool:
    """Validar formato de email"""
    patron = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if not re.match(patron, email):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Formato de email inválido"
        )
    return True

def validar_nombre_completo(nombre: str, apellido: str) -> bool:
    """Validar nombre y apellido"""
    if not nombre or not apellido:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Nombre y apellido son obligatorios"
        )
    
    if len(nombre) < 2 or len(apellido) < 2:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Nombre y apellido deben tener al menos 2 caracteres"
        )
    
    if not nombre.replace(" ", "").isalpha() or not apellido.replace(" ", "").isalpha():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Nombre y apellido solo pueden contener letras y espacios"
        )
    
    return True

def validar_telefono(telefono: str) -> bool:
    """Validar formato de teléfono"""
    if not telefono:
        return True
    
    # Remover espacios, guiones, paréntesis
    telefono_limpio = re.sub(r'[\s\-\(\)]', '', telefono)
    
    # Validar que solo contenga números y tenga entre 8 y 15 dígitos
    if not telefono_limpio.isdigit() or len(telefono_limpio) < 8 or len(telefono_limpio) > 15:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Formato de teléfono inválido"
        )
    
    return True