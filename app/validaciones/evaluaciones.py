from fastapi import HTTPException, status

def validar_puntuacion_evaluacion(puntuacion: float, campo: str = "puntuacion") -> bool:
    """Validar puntuación de evaluación (0-100)"""
    if puntuacion is None:
        return True
    
    if puntuacion < 0 or puntuacion > 100:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"{campo} debe estar entre 0 y 100"
        )
    
    return True

def validar_velocidad_lectura(velocidad: float) -> bool:
    """Validar velocidad de lectura (palabras por minuto)"""
    if velocidad is None:
        return True
    
    if velocidad < 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="La velocidad de lectura no puede ser negativa"
        )
    
    if velocidad > 500:  # Límite razonable para niños
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Velocidad de lectura fuera de rango válido"
        )
    
    return True

def validar_fluidez(fluidez: float) -> bool:
    """Validar puntuación de fluidez (0-100)"""
    return validar_puntuacion_evaluacion(fluidez, "Fluidez")

def validar_precision_palabras(precision: float) -> bool:
    """Validar precisión de palabras (0-100)"""
    return validar_puntuacion_evaluacion(precision, "Precisión de palabras")

def validar_severidad_error(severidad: int) -> bool:
    """Validar severidad de error (1-5)"""
    if severidad is None:
        return True
    
    if severidad < 1 or severidad > 5:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="La severidad del error debe estar entre 1 y 5"
        )
    
    return True