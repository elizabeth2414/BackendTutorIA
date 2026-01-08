# app/servicios/padre.py

from sqlalchemy.orm import Session
from app.modelos import Padre, Estudiante
from app.esquemas.padre import PadreCreate, PadreUpdate


# CRUD ================================================================

def crear_padre(db: Session, datos: PadreCreate):
    nuevo_padre = Padre(
        usuario_id=datos.usuario_id,
        telefono_contacto=datos.telefono_contacto,
        parentesco=datos.parentesco,
        notificaciones_activas=datos.notificaciones_activas,
        activo=datos.activo,
    )
    db.add(nuevo_padre)
    db.commit()
    db.refresh(nuevo_padre)
    return nuevo_padre


def obtener_padres(db: Session, skip: int = 0, limit: int = 100):
    return db.query(Padre).offset(skip).limit(limit).all()


def obtener_padre(db: Session, padre_id: int):
    return db.query(Padre).filter(Padre.id == padre_id).first()


def obtener_padre_por_usuario(db: Session, usuario_id: int):
    return db.query(Padre).filter(Padre.usuario_id == usuario_id).first()


def actualizar_padre(db: Session, padre_id: int, datos: PadreUpdate):
    padre = obtener_padre(db, padre_id)
    if not padre:
        return None

    for key, value in datos.dict(exclude_unset=True).items():
        setattr(padre, key, value)

    db.commit()
    db.refresh(padre)
    return padre


def eliminar_padre(db: Session, padre_id: int):
    padre = obtener_padre(db, padre_id)
    if not padre:
        return None

    db.delete(padre)
    db.commit()
    return True


# EXTRA ================================================================

def obtener_hijos(db: Session, padre_id: int):
    return db.query(Estudiante).filter(Estudiante.padre_id == padre_id).all()
