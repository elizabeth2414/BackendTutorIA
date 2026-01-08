from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from app.config import get_db
from app.esquemas.auth import UsuarioResponse, UsuarioUpdate, UsuarioRolCreate, UsuarioRolResponse
from app.servicios.usuario import (
    obtener_usuarios, obtener_usuario, actualizar_usuario,
    eliminar_usuario, crear_rol_usuario, obtener_roles_usuario
)
from app.servicios.seguridad import obtener_usuario_actual
from app.modelos import Usuario

router = APIRouter(prefix="/usuarios", tags=["usuarios"])

@router.get("/", response_model=List[UsuarioResponse])
def listar_usuarios(
    skip: int = 0,
    limit: int = 100,
    activo: Optional[bool] = None,
    db: Session = Depends(get_db),
    usuario_actual: Usuario = Depends(obtener_usuario_actual)
):
    """Listar todos los usuarios (solo admin)"""
    return obtener_usuarios(db, skip=skip, limit=limit, activo=activo)

@router.get("/{usuario_id}", response_model=UsuarioResponse)
def obtener_usuario_por_id(
    usuario_id: int,
    db: Session = Depends(get_db),
    usuario_actual: Usuario = Depends(obtener_usuario_actual)
):
    """Obtener usuario por ID"""
    db_usuario = obtener_usuario(db, usuario_id)
    if not db_usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    return db_usuario

@router.put("/{usuario_id}", response_model=UsuarioResponse)
def actualizar_usuario_por_id(
    usuario_id: int,
    usuario: UsuarioUpdate,
    db: Session = Depends(get_db),
    usuario_actual: Usuario = Depends(obtener_usuario_actual)
):
    """Actualizar usuario"""
    return actualizar_usuario(db, usuario_id, usuario)

@router.delete("/{usuario_id}")
def eliminar_usuario_por_id(
    usuario_id: int,
    db: Session = Depends(get_db),
    usuario_actual: Usuario = Depends(obtener_usuario_actual)
):
    """Eliminar usuario (soft delete)"""
    eliminar_usuario(db, usuario_id)
    return {"mensaje": "Usuario eliminado correctamente"}

@router.post("/{usuario_id}/roles", response_model=UsuarioRolResponse)
def agregar_rol_usuario(
    usuario_id: int,
    rol: UsuarioRolCreate,
    db: Session = Depends(get_db),
    usuario_actual: Usuario = Depends(obtener_usuario_actual)
):
    """Agregar rol a usuario"""
    return crear_rol_usuario(db, usuario_id, rol)

@router.get("/{usuario_id}/roles", response_model=List[UsuarioRolResponse])
def listar_roles_usuario(
    usuario_id: int,
    db: Session = Depends(get_db),
    usuario_actual: Usuario = Depends(obtener_usuario_actual)
):
    """Obtener roles de un usuario"""
    return obtener_roles_usuario(db, usuario_id)