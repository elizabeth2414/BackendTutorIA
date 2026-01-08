from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from typing import List, Optional

from app.modelos import ContenidoLectura, CategoriaLectura, AudioReferencia
from app.esquemas.contenido import ContenidoLecturaCreate, ContenidoLecturaUpdate, CategoriaLecturaCreate, CategoriaLecturaUpdate, AudioReferenciaCreate

def crear_contenido_lectura(db: Session, contenido: ContenidoLecturaCreate):
    db_contenido = ContenidoLectura(**contenido.dict())
    db.add(db_contenido)
    db.commit()
    db.refresh(db_contenido)
    return db_contenido

def obtener_contenidos(db: Session, skip: int = 0, limit: int = 100, 
                      curso_id: Optional[int] = None, categoria_id: Optional[int] = None,
                      docente_id: Optional[int] = None, activo: Optional[bool] = None):
    query = db.query(ContenidoLectura)
    if curso_id is not None:
        query = query.filter(ContenidoLectura.curso_id == curso_id)
    if categoria_id is not None:
        query = query.filter(ContenidoLectura.categoria_id == categoria_id)
    if docente_id is not None:
        query = query.filter(ContenidoLectura.docente_id == docente_id)
    if activo is not None:
        query = query.filter(ContenidoLectura.activo == activo)
    return query.offset(skip).limit(limit).all()

def obtener_contenido(db: Session, contenido_id: int):
    return db.query(ContenidoLectura).filter(ContenidoLectura.id == contenido_id).first()

def actualizar_contenido(db: Session, contenido_id: int, contenido: ContenidoLecturaUpdate):
    db_contenido = obtener_contenido(db, contenido_id)
    if not db_contenido:
        raise HTTPException(status_code=404, detail="Contenido no encontrado")
    
    update_data = contenido.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_contenido, field, value)
    
    db.commit()
    db.refresh(db_contenido)
    return db_contenido

def eliminar_contenido(db: Session, contenido_id: int):
    db_contenido = obtener_contenido(db, contenido_id)
    if not db_contenido:
        raise HTTPException(status_code=404, detail="Contenido no encontrado")
    
    # Soft delete
    db_contenido.activo = False
    db.commit()
    return db_contenido

def crear_categoria_lectura(db: Session, categoria: CategoriaLecturaCreate):
    db_categoria = CategoriaLectura(**categoria.dict())
    db.add(db_categoria)
    db.commit()
    db.refresh(db_categoria)
    return db_categoria

def obtener_categorias(db: Session, skip: int = 0, limit: int = 100, activo: Optional[bool] = None):
    query = db.query(CategoriaLectura)
    if activo is not None:
        query = query.filter(CategoriaLectura.activo == activo)
    return query.offset(skip).limit(limit).all()

def obtener_categoria(db: Session, categoria_id: int):
    return db.query(CategoriaLectura).filter(CategoriaLectura.id == categoria_id).first()

def actualizar_categoria(db: Session, categoria_id: int, categoria: CategoriaLecturaUpdate):
    db_categoria = obtener_categoria(db, categoria_id)
    if not db_categoria:
        raise HTTPException(status_code=404, detail="Categoría no encontrada")
    
    update_data = categoria.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_categoria, field, value)
    
    db.commit()
    db.refresh(db_categoria)
    return db_categoria

def eliminar_categoria(db: Session, categoria_id: int):
    db_categoria = obtener_categoria(db, categoria_id)
    if not db_categoria:
        raise HTTPException(status_code=404, detail="Categoría no encontrada")
    
    # Soft delete
    db_categoria.activo = False
    db.commit()
    return db_categoria

def crear_audio_referencia(db: Session, audio: AudioReferenciaCreate):
    db_audio = AudioReferencia(**audio.dict())
    db.add(db_audio)
    db.commit()
    db.refresh(db_audio)
    return db_audio

def obtener_audios_contenido(db: Session, contenido_id: int):
    return db.query(AudioReferencia).filter(AudioReferencia.contenido_id == contenido_id).all()