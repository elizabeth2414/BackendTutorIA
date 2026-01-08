from fastapi import HTTPException, status
from typing import List

def validar_edad_contenido(edad_recomendada: int) -> bool:
    """Validar edad recomendada para contenido (5-12 años)"""
    if edad_recomendada < 5 or edad_recomendada > 12:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="La edad recomendada debe estar entre 5 y 12 años"
        )
    return True

def validar_dificultad_contenido(nivel_dificultad: int) -> bool:
    """Validar nivel de dificultad (1-5)"""
    if nivel_dificultad < 1 or nivel_dificultad > 5:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El nivel de dificultad debe estar entre 1 y 5"
        )
    return True

def validar_palabras_clave(palabras_clave: List[str]) -> bool:
    """Validar lista de palabras clave"""
    if palabras_clave is None:
        return True
    
    if len(palabras_clave) > 20:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Máximo 20 palabras clave permitidas"
        )
    
    for palabra in palabras_clave:
        if len(palabra) > 50:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cada palabra clave debe tener máximo 50 caracteres"
            )
    
    return True

def validar_longitud_contenido(contenido: str) -> bool:
    """Validar longitud del contenido"""
    if len(contenido) < 10:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El contenido debe tener al menos 10 caracteres"
        )
    
    if len(contenido) > 10000:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El contenido no puede exceder los 10,000 caracteres"
        )
    
    return True

def validar_titulo_contenido(titulo: str) -> bool:
    """Validar título del contenido"""
    if len(titulo) < 5:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El título debe tener al menos 5 caracteres"
        )
    
    if len(titulo) > 300:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El título no puede exceder los 300 caracteres"
        )
    
    return True