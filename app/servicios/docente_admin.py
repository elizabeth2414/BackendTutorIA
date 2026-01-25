from typing import List, Optional
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from datetime import datetime

from app.modelos import Usuario, UsuarioRol, Docente
from app.esquemas.docente import DocenteCreateAdmin, DocenteUpdate
from app.servicios.seguridad import obtener_password_hash


# ===========================================================
# CREAR DOCENTE
# ===========================================================
def crear_docente_admin(db: Session, data: DocenteCreateAdmin) -> Docente:

    # 1. Validar email repetido (solo usuarios NO eliminados)
    if db.query(Usuario).filter(
        Usuario.email == data.email,
        Usuario.deleted_at.is_(None)  # ← Solo no eliminados
    ).first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Ya existe un usuario con ese email",
        )

    try:
        # 2. Convertir fecha (si viene vacía la ponemos como None)
        fecha_contratacion = None
        if data.fecha_contratacion not in ["", None]:
            fecha_contratacion = datetime.strptime(
                str(data.fecha_contratacion), "%Y-%m-%d"
            ).date()

        # 3. Crear usuario
        usuario = Usuario(
            email=data.email,
            password_hash=obtener_password_hash(data.password),
            nombre=data.nombre,
            apellido=data.apellido,
            activo=True,
        )
        db.add(usuario)
        db.flush()  # obtener usuario.id

        # 4. Asignar rol docente
        rol = UsuarioRol(
            usuario_id=usuario.id,
            rol="docente",
            activo=True,
        )
        db.add(rol)

        # 5. Crear docente
        docente = Docente(
            usuario_id=usuario.id,
            especialidad=data.especialidad,
            grado_academico=data.grado_academico,
            institucion=data.institucion,
            fecha_contratacion=fecha_contratacion,
            activo=True,
        )
        db.add(docente)

        # 6. Guardar cambios
        db.commit()
        db.refresh(docente)

        return docente

    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Error interno al crear docente: {str(e)}",
        )


# ===========================================================
# LISTAR DOCENTES (Solo NO eliminados)
# ===========================================================
def listar_docentes_admin(db: Session, activo: Optional[bool] = None) -> List[Docente]:
    """
    Lista solo docentes que NO están eliminados.
    """
    query = db.query(Docente).filter(
        Docente.deleted_at.is_(None)  # ← Solo no eliminados
    )

    # Filtrar por activo si se especifica
    if activo is not None:
        query = query.filter(Docente.activo == activo)

    return query.all()


# ===========================================================
# OBTENER DOCENTE (Solo si NO está eliminado)
# ===========================================================
def obtener_docente_admin(db: Session, docente_id: int) -> Docente:
    """
    Obtiene un docente solo si NO está eliminado.
    """
    docente = db.query(Docente).filter(
        Docente.id == docente_id,
        Docente.deleted_at.is_(None)  # ← Solo no eliminados
    ).first()
    
    if not docente:
        raise HTTPException(404, "Docente no encontrado")
    
    return docente


# ===========================================================
# ACTUALIZAR DOCENTE
# ===========================================================
def actualizar_docente_admin(db: Session, docente_id: int, data: DocenteUpdate):
    """
    Actualiza un docente (solo si NO está eliminado).
    """
    # Buscar docente (solo no eliminados)
    docente = db.query(Docente).filter(
        Docente.id == docente_id,
        Docente.deleted_at.is_(None)  # ← Solo no eliminados
    ).first()
    
    if not docente:
        raise HTTPException(status_code=404, detail="Docente no encontrado")
    
    # Buscar usuario asociado
    usuario = db.query(Usuario).filter(Usuario.id == docente.usuario_id).first()
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    
    # Actualizar campos del USUARIO (si vienen en data)
    if data.nombre is not None:
        usuario.nombre = data.nombre
    if data.apellido is not None:
        usuario.apellido = data.apellido
    if data.email is not None:
        # Verificar email único (solo entre usuarios NO eliminados)
        email_existe = db.query(Usuario).filter(
            Usuario.email == data.email,
            Usuario.id != usuario.id,
            Usuario.deleted_at.is_(None)  # ← Solo no eliminados
        ).first()
        if email_existe:
            raise HTTPException(400, detail="El email ya está registrado")
        usuario.email = data.email
    
    # Actualizar campos del DOCENTE (si vienen en data)
    if data.especialidad is not None:
        docente.especialidad = data.especialidad
    if data.grado_academico is not None:
        docente.grado_academico = data.grado_academico
    if data.institucion is not None:
        docente.institucion = data.institucion
    if data.fecha_contratacion is not None:
        docente.fecha_contratacion = data.fecha_contratacion
    if data.activo is not None:
        docente.activo = data.activo
        usuario.activo = data.activo
    
    # Actualizar fecha de modificación del usuario
    usuario.fecha_actualizacion = datetime.utcnow()
    
    # Guardar cambios
    db.commit()
    db.refresh(docente)
    db.refresh(usuario)
    
    return docente


# ===========================================================
# TOGGLE ACTIVO/INACTIVO
# ===========================================================
def toggle_docente_admin(db: Session, docente_id: int):
    """
    Activa o desactiva un docente (sin eliminarlo).
    Solo funciona con docentes NO eliminados.
    """
    docente = db.query(Docente).filter(
        Docente.id == docente_id,
        Docente.deleted_at.is_(None)  # ← Solo no eliminados
    ).first()
    
    if not docente:
        raise HTTPException(status_code=404, detail="Docente no encontrado")
    
    # Cambiar estado (toggle)
    docente.activo = not docente.activo
    
    # Cambiar estado del usuario también
    if docente.usuario:
        docente.usuario.activo = docente.activo
    
    db.commit()
    db.refresh(docente)
    
    return docente


# ===========================================================
# ELIMINAR DOCENTE (Soft Delete con deleted_at)
# ===========================================================
def eliminar_docente_admin(db: Session, docente_id: int):
    """
    Soft delete: Marca fecha de eliminación usando deleted_at.
    - NO elimina físicamente de la base de datos
    - Marca deleted_at con timestamp actual
    - También marca activo = False
    - Se puede recuperar si es necesario
    - NUNCA falla por foreign key constraints
    """
    # Buscar docente (solo no eliminados)
    docente = db.query(Docente).filter(
        Docente.id == docente_id,
        Docente.deleted_at.is_(None)  # ← Solo no eliminados
    ).first()
    
    if not docente:
        raise HTTPException(status_code=404, detail="Docente no encontrado")
    
    try:
        # Marcar como eliminado con timestamp actual
        ahora = datetime.utcnow()
        docente.deleted_at = ahora
        docente.activo = False
        
        # Marcar usuario como eliminado también
        if docente.usuario:
            docente.usuario.deleted_at = ahora
            docente.usuario.activo = False
        
        db.commit()
        
        return {"mensaje": "Docente eliminado correctamente"}
    
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Error al eliminar docente: {str(e)}"
        )


# ===========================================================
# RESTAURAR DOCENTE (OPCIONAL - Si quieres recuperar eliminados)
# ===========================================================
def restaurar_docente_admin(db: Session, docente_id: int):
    """
    Restaura un docente eliminado (soft delete).
    - Elimina deleted_at (pone en NULL)
    - Reactiva el docente y usuario
    """
    # Buscar docente eliminado
    docente = db.query(Docente).filter(
        Docente.id == docente_id,
        Docente.deleted_at.isnot(None)  # ← Solo eliminados
    ).first()
    
    if not docente:
        raise HTTPException(status_code=404, detail="Docente eliminado no encontrado")
    
    try:
        # Restaurar docente
        docente.deleted_at = None
        docente.activo = True
        
        # Restaurar usuario
        if docente.usuario:
            docente.usuario.deleted_at = None
            docente.usuario.activo = True
        
        db.commit()
        db.refresh(docente)
        
        return {"mensaje": "Docente restaurado correctamente"}
    
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Error al restaurar docente: {str(e)}"
        )
    