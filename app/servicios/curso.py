from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from typing import Optional
import secrets
import string

from app.modelos import Curso, EstudianteCurso
from app.esquemas.curso import CursoCreate, CursoUpdate


def generar_codigo_acceso(length: int = 8) -> str:
    """Genera un código de acceso único."""
    alphabet = string.ascii_uppercase + string.digits
    return ''.join(secrets.choice(alphabet) for _ in range(length))



def crear_curso(db: Session, curso: CursoCreate):
    """
    Crea un nuevo curso con código de acceso único.
    """
    # Generar código de acceso único
    codigo = generar_codigo_acceso()
    while db.query(Curso).filter(Curso.codigo_acceso == codigo).first():
        codigo = generar_codigo_acceso()

    # Tomamos los datos del esquema, pero excluimos 'codigo_acceso'
    data = curso.dict(exclude_unset=True, exclude={"codigo_acceso"})

    # Asignamos nuestro código generado
    data["codigo_acceso"] = codigo

    db_curso = Curso(**data)
    db.add(db_curso)
    db.commit()
    db.refresh(db_curso)
    return db_curso



def obtener_cursos(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    docente_id: Optional[int] = None,
    activo: Optional[bool] = None
):
    """
    Lista cursos con filtros opcionales.
    
    Args:
        db: Sesión de base de datos
        skip: Offset para paginación
        limit: Límite de resultados
        docente_id: Filtrar por docente específico
        activo: Filtrar por estado activo/inactivo
    
    Returns:
        Lista de cursos
    """
    query = db.query(Curso)
    
    # Si el modelo tiene deleted_at, filtrar cursos eliminados
    if hasattr(Curso, 'deleted_at'):
        query = query.filter(Curso.deleted_at.is_(None))
    
    if docente_id is not None:
        query = query.filter(Curso.docente_id == docente_id)
    
    if activo is not None:
        query = query.filter(Curso.activo == activo)
    
    return query.offset(skip).limit(limit).all()



def obtener_cursos_activos(
    db: Session,
    docente_id: Optional[int] = None
):
    """
    Lista SOLO cursos activos.
    Úsala para combobox, selects, asignaciones, etc.
    
    Args:
        db: Sesión de base de datos
        docente_id: Filtrar por docente específico (opcional)
    
    Returns:
        Lista de cursos activos
    """
    query = db.query(Curso).filter(Curso.activo == True)
    
    # Si tiene deleted_at, filtrar también
    if hasattr(Curso, 'deleted_at'):
        query = query.filter(Curso.deleted_at.is_(None))
    
    if docente_id is not None:
        query = query.filter(Curso.docente_id == docente_id)
    
    return query.all()



def obtener_curso(db: Session, curso_id: int):
    """
    Obtiene un curso por ID (solo si NO está eliminado).
    """
    query = db.query(Curso).filter(Curso.id == curso_id)
    
    # Si tiene deleted_at, filtrar eliminados
    if hasattr(Curso, 'deleted_at'):
        query = query.filter(Curso.deleted_at.is_(None))
    
    return query.first()


def obtener_curso_por_codigo(db: Session, codigo_acceso: str):
    """
    Obtiene un curso por código de acceso (solo si NO está eliminado).
    """
    query = db.query(Curso).filter(Curso.codigo_acceso == codigo_acceso)
    
    # Si tiene deleted_at, filtrar eliminados
    if hasattr(Curso, 'deleted_at'):
        query = query.filter(Curso.deleted_at.is_(None))
    
    return query.first()



def actualizar_curso(db: Session, curso_id: int, curso: CursoUpdate):
    """
    Actualiza un curso existente.
    """
    db_curso = obtener_curso(db, curso_id)
    if not db_curso:
        raise HTTPException(status_code=404, detail="Curso no encontrado")

    update_data = curso.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_curso, field, value)

    db.commit()
    db.refresh(db_curso)
    return db_curso



def validar_relaciones_curso(db: Session, curso_id: int):
    """
    Valida si un curso tiene relaciones que impiden su eliminación.
    
    Args:
        db: Sesión de base de datos
        curso_id: ID del curso a validar
    
    Returns:
        dict: {
            "tiene_relaciones": bool,
            "detalles": {
                "estudiantes": int,
                "lecturas": int,
                "actividades": int
            }
        }
    """
    # Contar estudiantes inscritos
    estudiantes_count = db.query(EstudianteCurso).filter(
        EstudianteCurso.curso_id == curso_id
    ).count()
    
    
    lecturas_count = 0
    try:
        from app.modelos.lectura import Lectura
        lecturas_count = db.query(Lectura).filter(
            Lectura.curso_id == curso_id
        ).count()
    except ImportError:
        pass 
    
   
    actividades_count = 0
    try:
        from app.modelos.actividad import Actividad
        actividades_count = db.query(Actividad).filter(
            Actividad.curso_id == curso_id
        ).count()
    except ImportError:
        pass  
   
    tiene_relaciones = (
        estudiantes_count > 0 or 
        lecturas_count > 0 or 
        actividades_count > 0
    )
    
    detalles = {
        "estudiantes": estudiantes_count,
        "lecturas": lecturas_count,
        "actividades": actividades_count
    }
    
    return {
        "tiene_relaciones": tiene_relaciones,
        "detalles": detalles
    }



def eliminar_curso(db: Session, curso_id: int):
    """
    Elimina un curso SOLO si no tiene relaciones.
    
    Args:
        db: Sesión de base de datos
        curso_id: ID del curso a eliminar
    
    Returns:
        dict: Mensaje de éxito
    
    Raises:
        HTTPException 404: Si el curso no existe
        HTTPException 400: Si el curso tiene relaciones
    """
    db_curso = obtener_curso(db, curso_id)
    if not db_curso:
        raise HTTPException(status_code=404, detail="Curso no encontrado")
    
    # Validar relaciones
    validacion = validar_relaciones_curso(db, curso_id)
    
    if validacion["tiene_relaciones"]:
        detalles = validacion["detalles"]
        mensajes = []
        
        if detalles["estudiantes"] > 0:
            mensajes.append(f"{detalles['estudiantes']} estudiante(s) inscrito(s)")
        if detalles["lecturas"] > 0:
            mensajes.append(f"{detalles['lecturas']} lectura(s)")
        if detalles["actividades"] > 0:
            mensajes.append(f"{detalles['actividades']} actividad(es)")
        
        raise HTTPException(
            status_code=400,
            detail=f"No se puede eliminar el curso. Tiene datos relacionados: {', '.join(mensajes)}. Desactívalo en su lugar o elimina primero los datos relacionados."
        )
    
    # Si no tiene relaciones, eliminar
    try:
        db.delete(db_curso)
        db.commit()
        
        return {
            "mensaje": "Curso eliminado correctamente",
            "curso_id": curso_id
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Error al eliminar curso: {str(e)}"
        )



def toggle_curso_activo(db: Session, curso_id: int):
    """
    Activa o desactiva un curso.
    
    Args:
        db: Sesión de base de datos
        curso_id: ID del curso
    
    Returns:
        Curso actualizado
    """
    db_curso = obtener_curso(db, curso_id)
    if not db_curso:
        raise HTTPException(status_code=404, detail="Curso no encontrado")
    
    # Toggle estado
    db_curso.activo = not db_curso.activo
    
    db.commit()
    db.refresh(db_curso)
    
    return db_curso



def inscribir_estudiante(db: Session, curso_id: int, estudiante_id: int):
    """
    Inscribe un estudiante en un curso.
    Solo permite inscripción si el curso está activo.
    """
    # Verificar que el curso existe y está activo
    curso = obtener_curso(db, curso_id)
    if not curso:
        raise HTTPException(status_code=404, detail="Curso no encontrado")
    
    if not curso.activo:
        raise HTTPException(
            status_code=400,
            detail="No se puede inscribir en un curso inactivo"
        )

    # Verificar que el estudiante existe
    from app.servicios.estudiante import obtener_estudiante
    estudiante = obtener_estudiante(db, estudiante_id)
    if not estudiante:
        raise HTTPException(status_code=404, detail="Estudiante no encontrado")

    # Verificar que no esté ya inscrito
    existente = db.query(EstudianteCurso).filter(
        EstudianteCurso.curso_id == curso_id,
        EstudianteCurso.estudiante_id == estudiante_id
    ).first()
    if existente:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El estudiante ya está inscrito en este curso"
        )

    db_inscripcion = EstudianteCurso(curso_id=curso_id, estudiante_id=estudiante_id)
    db.add(db_inscripcion)
    db.commit()
    db.refresh(db_inscripcion)
    return db_inscripcion



def obtener_estudiantes_curso(db: Session, curso_id: int):
    """Lista estudiantes inscritos en un curso."""
    return db.query(EstudianteCurso).filter(
        EstudianteCurso.curso_id == curso_id
    ).all()



def obtener_cursos_estudiante(db: Session, estudiante_id: int):
    """
    Lista cursos en los que está inscrito un estudiante.
    Solo retorna cursos activos.
    """
    # Obtener IDs de cursos del estudiante
    inscripciones = db.query(EstudianteCurso).filter(
        EstudianteCurso.estudiante_id == estudiante_id
    ).all()
    
    curso_ids = [i.curso_id for i in inscripciones]
    
    if not curso_ids:
        return []
    
    # Obtener solo cursos activos
    query = db.query(Curso).filter(
        Curso.id.in_(curso_ids),
        Curso.activo == True
    )
    
    # Si tiene deleted_at, filtrar eliminados
    if hasattr(Curso, 'deleted_at'):
        query = query.filter(Curso.deleted_at.is_(None))
    
    return query.all()
