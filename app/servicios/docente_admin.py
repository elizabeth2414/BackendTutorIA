from typing import List, Optional
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from datetime import datetime, timedelta, timezone

from app.modelos import Usuario, UsuarioRol, Docente, Estudiante
from app.esquemas.docente import DocenteCreateAdmin, DocenteUpdate
from app.servicios.seguridad import obtener_password_hash
from app.servicios.email_service import email_service
import secrets


def now_utc() -> datetime:
    return datetime.now(timezone.utc)


def _contar_estudiantes_activos(db: Session, docente_id: int) -> int:
    # ✅ Cuenta alumnos asignados NO eliminados (y opcionalmente activos)
    return (
        db.query(Estudiante)
        .filter(
            Estudiante.docente_id == docente_id,
            Estudiante.deleted_at.is_(None),
            Estudiante.activo.is_(True),
        )
        .count()
    )


def crear_docente_admin(db: Session, data: DocenteCreateAdmin) -> Docente:
    """
    ✅ Crea docente si el email NO existe.
    ✅ Si el email existe pero estaba eliminado (soft delete), RESTAURA y reutiliza el mismo usuario/docente.
    """

    try:
        # Buscar usuario por email (SIN filtrar deleted_at, porque el unique del email vive siempre)
        usuario_existente = db.query(Usuario).filter(Usuario.email == data.email).first()

        # Parse fecha
        fecha_contratacion = None
        if data.fecha_contratacion not in ["", None]:
            fecha_contratacion = datetime.strptime(str(data.fecha_contratacion), "%Y-%m-%d").date()

        # Generar password temporal y token de setup
        password_temporal = secrets.token_urlsafe(32)
        password_hash_temp = obtener_password_hash(password_temporal)

        setup_token = secrets.token_urlsafe(32)
        setup_expira = now_utc() + timedelta(hours=48)

        # ------------------------------------------------------------------
        # CASO A: No existe usuario -> crear todo normal
        # ------------------------------------------------------------------
        if not usuario_existente:
            usuario = Usuario(
                email=data.email,
                password_hash=password_hash_temp,
                nombre=data.nombre,
                apellido=data.apellido,
                activo=True,
                email_verificado=False,
                token_reset_password=setup_token,
                token_reset_expira=setup_expira,
                token_reset_usado=False,
            )
            db.add(usuario)
            db.flush()

            rol = UsuarioRol(
                usuario_id=usuario.id,
                rol="docente",
                activo=True,
            )
            db.add(rol)

            docente = Docente(
                usuario_id=usuario.id,
                especialidad=data.especialidad,
                grado_academico=data.grado_academico,
                institucion=data.institucion,
                fecha_contratacion=fecha_contratacion,
                activo=True,
                deleted_at=None,
            )
            db.add(docente)

            db.commit()
            db.refresh(docente)

            try:
                email_service.send_setup_account_email(
                    to_email=usuario.email,
                    usuario_nombre=f"{usuario.nombre} {usuario.apellido}".strip(),
                    setup_token=setup_token,
                )
            except Exception:
                from app.logs.logger import logger
                logger.exception("No se pudo enviar correo de configuración al docente")

            return docente

        # ------------------------------------------------------------------
        # CASO B: Existe usuario
        #   - Si está eliminado -> RESTAURAR y reasignar rol/docente
        #   - Si NO está eliminado -> error (ya existe)
        # ------------------------------------------------------------------
        if usuario_existente.deleted_at is None:
            # Ya existe “vivo” (activo o inactivo), pero NO eliminado.
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Ya existe un usuario con ese email",
            )

        # ✅ RESTAURAR usuario eliminado
        usuario_existente.deleted_at = None
        usuario_existente.activo = True
        usuario_existente.nombre = data.nombre
        usuario_existente.apellido = data.apellido
        usuario_existente.email_verificado = False

        # refrescar credenciales/setup
        usuario_existente.password_hash = password_hash_temp
        usuario_existente.token_reset_password = setup_token
        usuario_existente.token_reset_expira = setup_expira
        usuario_existente.token_reset_usado = False

        # Asegurar rol docente activo
        rol_docente = (
            db.query(UsuarioRol)
            .filter(UsuarioRol.usuario_id == usuario_existente.id, UsuarioRol.rol == "docente")
            .first()
        )
        if rol_docente:
            rol_docente.activo = True
        else:
            db.add(UsuarioRol(usuario_id=usuario_existente.id, rol="docente", activo=True))

        # Asegurar docente asociado
        docente_existente = db.query(Docente).filter(Docente.usuario_id == usuario_existente.id).first()
        if docente_existente:
            docente_existente.deleted_at = None
            docente_existente.activo = True
            docente_existente.especialidad = data.especialidad
            docente_existente.grado_academico = data.grado_academico
            docente_existente.institucion = data.institucion
            docente_existente.fecha_contratacion = fecha_contratacion
            docente = docente_existente
        else:
            docente = Docente(
                usuario_id=usuario_existente.id,
                especialidad=data.especialidad,
                grado_academico=data.grado_academico,
                institucion=data.institucion,
                fecha_contratacion=fecha_contratacion,
                activo=True,
                deleted_at=None,
            )
            db.add(docente)

        db.commit()
        db.refresh(docente)

        # Enviar correo de setup nuevamente
        try:
            email_service.send_setup_account_email(
                to_email=usuario_existente.email,
                usuario_nombre=f"{usuario_existente.nombre} {usuario_existente.apellido}".strip(),
                setup_token=setup_token,
            )
        except Exception:
            from app.logs.logger import logger
            logger.exception("No se pudo reenviar correo de configuración al docente restaurado")

        return docente

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Error interno al crear docente: {str(e)}",
        )


def listar_docentes_admin(db: Session, activo: Optional[bool] = None) -> List[Docente]:
    """
    Lista docentes NO eliminados.
    """
    query = db.query(Docente).filter(Docente.deleted_at.is_(None))
    if activo is not None:
        query = query.filter(Docente.activo == activo)
    return query.all()


def listar_docentes_eliminados_admin(db: Session) -> List[Docente]:
    """
    Lista docentes eliminados (soft delete).
    """
    return db.query(Docente).filter(Docente.deleted_at.isnot(None)).all()


def obtener_docente_admin(db: Session, docente_id: int) -> Docente:
    docente = db.query(Docente).filter(Docente.id == docente_id, Docente.deleted_at.is_(None)).first()
    if not docente:
        raise HTTPException(404, "Docente no encontrado")
    return docente


def actualizar_docente_admin(db: Session, docente_id: int, data: DocenteUpdate) -> Docente:
    docente = db.query(Docente).filter(Docente.id == docente_id, Docente.deleted_at.is_(None)).first()
    if not docente:
        raise HTTPException(status_code=404, detail="Docente no encontrado")

    usuario = db.query(Usuario).filter(Usuario.id == docente.usuario_id).first()
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    # USUARIO
    if data.nombre is not None:
        usuario.nombre = data.nombre
    if data.apellido is not None:
        usuario.apellido = data.apellido
    if data.email is not None:
        email_existe = db.query(Usuario).filter(
            Usuario.email == data.email,
            Usuario.id != usuario.id,
        ).first()
        if email_existe:
            raise HTTPException(400, detail="El email ya está registrado")
        usuario.email = data.email

    # DOCENTE
    if data.especialidad is not None:
        docente.especialidad = data.especialidad
    if data.grado_academico is not None:
        docente.grado_academico = data.grado_academico
    if data.institucion is not None:
        docente.institucion = data.institucion
    if data.fecha_contratacion is not None:
        docente.fecha_contratacion = data.fecha_contratacion

    # ⚠️ Si piden desactivar por update, aplicar la misma regla de alumnos
    if data.activo is not None and data.activo is False and docente.activo is True:
        n = _contar_estudiantes_activos(db, docente.id)
        if n > 0:
            raise HTTPException(
                status_code=400,
                detail=f"No se puede desactivar: el docente tiene {n} estudiante(s) asignado(s).",
            )
        docente.activo = False
        usuario.activo = False
    elif data.activo is not None and data.activo is True:
        docente.activo = True
        usuario.activo = True

    usuario.fecha_actualizacion = now_utc()

    db.commit()
    db.refresh(docente)
    return docente


def toggle_docente_admin(db: Session, docente_id: int) -> Docente:
    """
    Activa o desactiva un docente (sin eliminarlo).
    ❌ Si tiene estudiantes activos asignados, NO permite desactivar.
    """
    docente = db.query(Docente).filter(Docente.id == docente_id, Docente.deleted_at.is_(None)).first()
    if not docente:
        raise HTTPException(status_code=404, detail="Docente no encontrado")

    # Si se va a desactivar, validar alumnos
    if docente.activo is True:
        n = _contar_estudiantes_activos(db, docente.id)
        if n > 0:
            raise HTTPException(
                status_code=400,
                detail=f"No se puede desactivar: el docente tiene {n} estudiante(s) asignado(s).",
            )

    docente.activo = not docente.activo

    if docente.usuario:
        docente.usuario.activo = docente.activo

    db.commit()
    db.refresh(docente)
    return docente


def eliminar_docente_admin(db: Session, docente_id: int):
    """
    Soft delete:
    ❌ Si tiene estudiantes activos asignados, NO permite eliminar.
    """
    docente = db.query(Docente).filter(Docente.id == docente_id, Docente.deleted_at.is_(None)).first()
    if not docente:
        raise HTTPException(status_code=404, detail="Docente no encontrado")

    n = _contar_estudiantes_activos(db, docente.id)
    if n > 0:
        raise HTTPException(
            status_code=400,
            detail=f"No se puede eliminar: el docente tiene {n} estudiante(s) asignado(s).",
        )

    try:
        ahora = now_utc()
        docente.deleted_at = ahora
        docente.activo = False

        if docente.usuario:
            docente.usuario.deleted_at = ahora
            docente.usuario.activo = False

        db.commit()
        return {"mensaje": "Docente eliminado correctamente"}

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error al eliminar docente: {str(e)}")


def restaurar_docente_admin(db: Session, docente_id: int) -> Docente:
    """
    Restaura un docente eliminado (soft delete).
    """
    docente = db.query(Docente).filter(Docente.id == docente_id, Docente.deleted_at.isnot(None)).first()
    if not docente:
        raise HTTPException(status_code=404, detail="Docente eliminado no encontrado")

    try:
        docente.deleted_at = None
        docente.activo = True

        if docente.usuario:
            docente.usuario.deleted_at = None
            docente.usuario.activo = True

        # Asegurar rol docente activo
        rol_docente = (
            db.query(UsuarioRol)
            .filter(UsuarioRol.usuario_id == docente.usuario_id, UsuarioRol.rol == "docente")
            .first()
        )
        if rol_docente:
            rol_docente.activo = True
        else:
            db.add(UsuarioRol(usuario_id=docente.usuario_id, rol="docente", activo=True))

        db.commit()
        db.refresh(docente)
        return docente

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error al restaurar docente: {str(e)}")
