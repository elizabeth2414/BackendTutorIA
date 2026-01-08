from datetime import date, datetime
from fastapi import HTTPException, status

def validar_edad_estudiante(fecha_nacimiento: date) -> bool:
    """Validar que la edad del estudiante esté entre 5 y 18 años"""
    hoy = date.today()
    edad = hoy.year - fecha_nacimiento.year - ((hoy.month, hoy.day) < (fecha_nacimiento.month, fecha_nacimiento.day))
    
    if edad < 5:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El estudiante debe tener al menos 5 años"
        )
    
    if edad > 18:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El estudiante no puede tener más de 18 años"
        )
    
    return True

def validar_nivel_educativo(nivel: int) -> bool:
    """Validar nivel educativo (1-6)"""
    if nivel < 1 or nivel > 6:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El nivel educativo debe estar entre 1 y 6"
        )
    return True

def validar_configuracion_estudiante(configuracion: dict) -> bool:
    """Validar configuración del estudiante"""
    if not configuracion:
        return True
    
    config_validas = {"sonidos", "animaciones", "dificultad", "tema", "velocidad_lectura"}
    
    for clave in configuracion.keys():
        if clave not in config_validas:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Configuración inválida: {clave}"
            )
    
    # Validar valores específicos
    if "dificultad" in configuracion:
        dificultades_validas = ["baja", "media", "alta"]
        if configuracion["dificultad"] not in dificultades_validas:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Dificultad debe ser: baja, media o alta"
            )
    
    if "sonidos" in configuracion and not isinstance(configuracion["sonidos"], bool):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Sonidos debe ser true o false"
        )
    
    return True