from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.modelos import Curso, EstudianteCurso

def validar_nivel_curso(nivel: int) -> bool:
    """Validar nivel del curso (1-6)"""
    if nivel < 1 or nivel > 6:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El nivel del curso debe estar entre 1 y 6"
        )
    return True

def validar_limite_estudiantes_curso(db: Session, curso_id: int) -> bool:
    """Validar que el curso no exceda el límite de estudiantes"""
    curso = db.query(Curso).filter(Curso.id == curso_id).first()
    if not curso:
        raise HTTPException(status_code=404, detail="Curso no encontrado")
    
    # Obtener configuración de límite de estudiantes
    configuracion = curso.configuracion or {}
    max_estudiantes = configuracion.get("max_estudiantes", 30)
    
    # Contar estudiantes activos
    count_estudiantes = db.query(EstudianteCurso).filter(
        EstudianteCurso.curso_id == curso_id,
        EstudianteCurso.estado == "activo"
    ).count()
    
    if count_estudiantes >= max_estudiantes:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"El curso ha alcanzado el límite máximo de {max_estudiantes} estudiantes"
        )
    
    return True

def validar_estudiante_no_inscrito(db: Session, curso_id: int, estudiante_id: int) -> bool:
    """Validar que el estudiante no esté ya inscrito en el curso"""
    inscripcion = db.query(EstudianteCurso).filter(
        EstudianteCurso.curso_id == curso_id,
        EstudianteCurso.estudiante_id == estudiante_id
    ).first()
    
    if inscripcion:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El estudiante ya está inscrito en este curso"
        )
    
    return True

def validar_configuracion_curso(configuracion: dict) -> bool:
    """Validar configuración del curso"""
    if not configuracion:
        return True
    
    config_validas = {"max_estudiantes", "publico", "auto_inscripcion", "mostrar_progreso"}
    
    for clave in configuracion.keys():
        if clave not in config_validas:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Configuración de curso inválida: {clave}"
            )
    
    # Validar valores específicos
    if "max_estudiantes" in configuracion:
        if not isinstance(configuracion["max_estudiantes"], int) or configuracion["max_estudiantes"] < 1:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="max_estudiantes debe ser un número mayor a 0"
            )
    
    if "publico" in configuracion and not isinstance(configuracion["publico"], bool):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="publico debe ser true o false"
        )
    
    return True