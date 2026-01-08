from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from typing import List, Optional

from app.modelos import Docente
from app.esquemas.docente import DocenteCreate, DocenteUpdate

def crear_docente(db: Session, docente: DocenteCreate):
    # Verificar si el usuario ya tiene un perfil de docente
    existente = db.query(Docente).filter(Docente.usuario_id == docente.usuario_id).first()
    if existente:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El usuario ya tiene un perfil de docente"
        )
    
    db_docente = Docente(**docente.dict())
    db.add(db_docente)
    db.commit()
    db.refresh(db_docente)
    return db_docente

def obtener_docentes(db: Session, skip: int = 0, limit: int = 100, activo: Optional[bool] = None):
    query = db.query(Docente)
    if activo is not None:
        query = query.filter(Docente.activo == activo)
    return query.offset(skip).limit(limit).all()

def obtener_docente(db: Session, docente_id: int):
    return db.query(Docente).filter(Docente.id == docente_id).first()

def obtener_docente_por_usuario(db: Session, usuario_id: int):
    return db.query(Docente).filter(Docente.usuario_id == usuario_id).first()

def actualizar_docente(db: Session, docente_id: int, docente: DocenteUpdate):
    db_docente = obtener_docente(db, docente_id)
    if not db_docente:
        raise HTTPException(status_code=404, detail="Docente no encontrado")
    
    update_data = docente.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_docente, field, value)
    
    db.commit()
    db.refresh(db_docente)
    return db_docente

def eliminar_docente(db: Session, docente_id: int):
    db_docente = obtener_docente(db, docente_id)
    if not db_docente:
        raise HTTPException(status_code=404, detail="Docente no encontrado")
    
    db_docente.activo = False
    db.commit()
    return db_docente