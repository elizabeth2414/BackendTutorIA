from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from typing import List, Optional

from app.modelos import Estudiante, NivelEstudiante, EstudianteCurso, Curso
from app.esquemas.estudiante import EstudianteCreate, EstudianteUpdate

def crear_estudiante(db: Session, estudiante: EstudianteCreate):
    # Si se proporciona usuario_id, verificar que no esté ya en uso
    if estudiante.usuario_id:
        existente = db.query(Estudiante).filter(Estudiante.usuario_id == estudiante.usuario_id).first()
        if existente:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El usuario ya tiene un perfil de estudiante"
            )
    
    db_estudiante = Estudiante(**estudiante.dict())
    db.add(db_estudiante)
    db.commit()
    db.refresh(db_estudiante)
    
    # Crear registro de nivel por defecto
    db_nivel = NivelEstudiante(estudiante_id=db_estudiante.id)
    db.add(db_nivel)
    db.commit()
    
    return db_estudiante

def obtener_estudiantes(db: Session, skip: int = 0, limit: int = 100, 
                       docente_id: Optional[int] = None, activo: Optional[bool] = None):
    query = db.query(Estudiante)
    if docente_id is not None:
        query = query.filter(Estudiante.docente_id == docente_id)
    if activo is not None:
        query = query.filter(Estudiante.activo == activo)
    return query.offset(skip).limit(limit).all()

def obtener_estudiante(db: Session, estudiante_id: int):
    return db.query(Estudiante).filter(Estudiante.id == estudiante_id).first()

def obtener_estudiante_por_usuario(db: Session, usuario_id: int):
    return db.query(Estudiante).filter(Estudiante.usuario_id == usuario_id).first()

def actualizar_estudiante(db: Session, estudiante_id: int, estudiante: EstudianteUpdate):
    db_estudiante = obtener_estudiante(db, estudiante_id)
    if not db_estudiante:
        raise HTTPException(status_code=404, detail="Estudiante no encontrado")
    
    update_data = estudiante.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_estudiante, field, value)
    
    db.commit()
    db.refresh(db_estudiante)
    return db_estudiante

def eliminar_estudiante(db: Session, estudiante_id: int):
    db_estudiante = obtener_estudiante(db, estudiante_id)
    if not db_estudiante:
        raise HTTPException(status_code=404, detail="Estudiante no encontrado")
    
    # Soft delete
    db_estudiante.activo = False
    db.commit()
    return db_estudiante

def obtener_nivel_estudiante(db: Session, estudiante_id: int):
    return db.query(NivelEstudiante).filter(NivelEstudiante.estudiante_id == estudiante_id).first()


def obtener_cursos_estudiante(db, estudiante_id: int):
    """
    Retorna la lista de cursos asociados a un estudiante.
    """
    cursos = (
        db.query(Curso)
        .join(EstudianteCurso, EstudianteCurso.curso_id == Curso.id)
        .filter(EstudianteCurso.estudiante_id == estudiante_id)
        .all()
    )
    return cursos
