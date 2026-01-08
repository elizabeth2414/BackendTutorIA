# app/servicios/actividad_lectura.py

from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from typing import List, Optional

from app.modelos import ActividadLectura, ContenidoLectura
from app.esquemas.actividad_lectura import ActividadLecturaCreate, ActividadLecturaUpdate
from app.logs.logger import logger


def crear_actividad_lectura(db: Session, actividad: ActividadLecturaCreate):
    """Crear una nueva actividad de lectura"""

    # Verificar que existe el contenido de lectura
    lectura = db.query(ContenidoLectura).filter(
        ContenidoLectura.id == actividad.lectura_id
    ).first()

    if not lectura:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Contenido de lectura con ID {actividad.lectura_id} no encontrado"
        )

    db_actividad = ActividadLectura(**actividad.model_dump())
    db.add(db_actividad)
    db.commit()
    db.refresh(db_actividad)

    logger.info(f"Actividad de lectura creada: ID={db_actividad.id}, Tipo={db_actividad.tipo}")
    return db_actividad


def obtener_actividades_lectura(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    lectura_id: Optional[int] = None,
    tipo: Optional[str] = None,
    activo: Optional[bool] = None
):
    """Obtener lista de actividades de lectura con filtros opcionales"""

    query = db.query(ActividadLectura)

    if lectura_id is not None:
        query = query.filter(ActividadLectura.lectura_id == lectura_id)

    if tipo:
        query = query.filter(ActividadLectura.tipo == tipo)

    if activo is not None:
        query = query.filter(ActividadLectura.activo == activo)

    return query.offset(skip).limit(limit).all()


def obtener_actividad_lectura(db: Session, actividad_id: int):
    """Obtener una actividad de lectura por ID"""

    actividad = db.query(ActividadLectura).filter(
        ActividadLectura.id == actividad_id
    ).first()

    if not actividad:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Actividad de lectura con ID {actividad_id} no encontrada"
        )

    return actividad


def actualizar_actividad_lectura(
    db: Session,
    actividad_id: int,
    actividad: ActividadLecturaUpdate
):
    """Actualizar una actividad de lectura"""

    db_actividad = obtener_actividad_lectura(db, actividad_id)

    # Actualizar solo los campos proporcionados
    update_data = actividad.model_dump(exclude_unset=True)

    for field, value in update_data.items():
        setattr(db_actividad, field, value)

    db.commit()
    db.refresh(db_actividad)

    logger.info(f"Actividad de lectura actualizada: ID={actividad_id}")
    return db_actividad


def eliminar_actividad_lectura(db: Session, actividad_id: int):
    """Eliminar (desactivar) una actividad de lectura"""

    db_actividad = obtener_actividad_lectura(db, actividad_id)

    # Soft delete - solo desactivar
    db_actividad.activo = False
    db.commit()

    logger.info(f"Actividad de lectura desactivada: ID={actividad_id}")
    return {"message": "Actividad de lectura desactivada exitosamente"}


def obtener_actividades_por_edad(
    db: Session,
    edad_estudiante: int,
    lectura_id: Optional[int] = None
):
    """Obtener actividades apropiadas para la edad del estudiante"""

    query = db.query(ActividadLectura).filter(
        ActividadLectura.edad_min <= edad_estudiante,
        ActividadLectura.edad_max >= edad_estudiante,
        ActividadLectura.activo == True
    )

    if lectura_id:
        query = query.filter(ActividadLectura.lectura_id == lectura_id)

    return query.all()


def obtener_actividades_generadas_ia(
    db: Session,
    lectura_id: Optional[int] = None,
    skip: int = 0,
    limit: int = 100
):
    """Obtener solo las actividades generadas por IA"""

    query = db.query(ActividadLectura).filter(
        ActividadLectura.origen == 'ia',
        ActividadLectura.activo == True
    )

    if lectura_id:
        query = query.filter(ActividadLectura.lectura_id == lectura_id)

    return query.offset(skip).limit(limit).all()
