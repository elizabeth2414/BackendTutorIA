from fastapi import HTTPException, status, Depends
from sqlalchemy.orm import Session
from typing import List

from app.config import get_db
from app.modelos import Usuario, UsuarioRol
from .autenticacion import obtener_usuario_actual

def obtener_roles_usuario(db: Session, usuario_id: int) -> List[str]:
    """Obtener roles activos de un usuario"""
    roles = db.query(UsuarioRol).filter(
        UsuarioRol.usuario_id == usuario_id,
        UsuarioRol.activo == True
    ).all()
    return [rol.rol for rol in roles]

def validar_roles(roles_permitidos: List[str] = None):
    """Decorador para validar roles de usuario"""
    def decorator(usuario_actual: Usuario = Depends(obtener_usuario_actual), db: Session = Depends(get_db)):
        if roles_permitidos is None:
            return usuario_actual
        
        roles_usuario = obtener_roles_usuario(db, usuario_actual.id)
        
        # Verificar si el usuario tiene al menos uno de los roles permitidos
        if not any(rol in roles_permitidos for rol in roles_usuario):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No tiene permisos suficientes para realizar esta acción"
            )
        
        return usuario_actual
    return decorator

# Funciones específicas de autorización
def es_admin(usuario_actual: Usuario = Depends(obtener_usuario_actual), db: Session = Depends(get_db)):
    """Verificar si el usuario es administrador"""
    return validar_roles(["admin"])(usuario_actual, db)

def es_docente(usuario_actual: Usuario = Depends(obtener_usuario_actual), db: Session = Depends(get_db)):
    """Verificar si el usuario es docente"""
    return validar_roles(["docente", "admin"])(usuario_actual, db)

def es_estudiante(usuario_actual: Usuario = Depends(obtener_usuario_actual), db: Session = Depends(get_db)):
    """Verificar si el usuario es estudiante"""
    return validar_roles(["estudiante", "docente", "admin"])(usuario_actual, db)

def es_padre(usuario_actual: Usuario = Depends(obtener_usuario_actual), db: Session = Depends(get_db)):
    """Verificar si el usuario es padre/tutor"""
    return validar_roles(["padre", "docente", "admin"])(usuario_actual, db)

def puede_ver_estudiante(estudiante_id: int, usuario_actual: Usuario = Depends(obtener_usuario_actual), db: Session = Depends(get_db)):
    """Verificar si el usuario puede ver los datos de un estudiante"""
    from app.modelos import Estudiante, Docente, AccesoPadre
    
    roles = obtener_roles_usuario(db, usuario_actual.id)
    
    if "admin" in roles:
        return usuario_actual
    
    if "docente" in roles:
        # Verificar si el docente es el dueño del estudiante
        docente = db.query(Docente).filter(Docente.usuario_id == usuario_actual.id).first()
        if docente:
            estudiante = db.query(Estudiante).filter(
                Estudiante.id == estudiante_id,
                Estudiante.docente_id == docente.id
            ).first()
            if estudiante:
                return usuario_actual
    
    if "padre" in roles:
        # Verificar si el padre tiene acceso al estudiante
        acceso = db.query(AccesoPadre).filter(
            AccesoPadre.estudiante_id == estudiante_id,
            AccesoPadre.padre_id == usuario_actual.id
        ).first()
        if acceso:
            return usuario_actual
    
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="No tiene permisos para ver este estudiante"
    )