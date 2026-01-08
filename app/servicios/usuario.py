from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from typing import List, Optional

from app.modelos import Usuario, UsuarioRol
from app.esquemas.auth import UsuarioUpdate, UsuarioRolCreate

def obtener_usuarios(db: Session, skip: int = 0, limit: int = 100, activo: Optional[bool] = None):
    query = db.query(Usuario)
    if activo is not None:
        query = query.filter(Usuario.activo == activo)
    return query.offset(skip).limit(limit).all()

def obtener_usuario(db: Session, usuario_id: int):
    return db.query(Usuario).filter(Usuario.id == usuario_id).first()

def actualizar_usuario(db: Session, usuario_id: int, usuario: UsuarioUpdate):
    db_usuario = obtener_usuario(db, usuario_id)
    if not db_usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    
    update_data = usuario.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_usuario, field, value)
    
    db.commit()
    db.refresh(db_usuario)
    return db_usuario

def eliminar_usuario(db: Session, usuario_id: int):
    db_usuario = obtener_usuario(db, usuario_id)
    if not db_usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    
    # Soft delete
    db_usuario.activo = False
    db.commit()
    return db_usuario

def crear_rol_usuario(db: Session, usuario_id: int, rol: UsuarioRolCreate):
    db_usuario = obtener_usuario(db, usuario_id)
    if not db_usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    
    db_rol = UsuarioRol(usuario_id=usuario_id, **rol.dict())
    db.add(db_rol)
    db.commit()
    db.refresh(db_rol)
    return db_rol

def obtener_roles_usuario(db: Session, usuario_id: int):
    return db.query(UsuarioRol).filter(UsuarioRol.usuario_id == usuario_id).all()