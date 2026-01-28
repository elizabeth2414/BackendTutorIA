from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from fastapi import HTTPException, status
from datetime import datetime, timedelta, timezone
import secrets

from app import settings
from app.modelos import Usuario, UsuarioRol
from app.esquemas.auth import UsuarioCreate, CambioPassword
from app.servicios.seguridad import verificar_password, obtener_password_hash
from app.servicios.email_service import email_service
from app.logs.logger import logger



def now_utc() -> datetime:
    return datetime.now(timezone.utc)




def autenticar_usuario(db: Session, email: str, password: str):
    """
    Autentica un usuario validando credenciales y estado de cuenta.
    
    Validaciones:
    1. Usuario existe
    2. Password correcto
    3. Email verificado
    4. Usuario NO eliminado (deleted_at is None)
    5. Usuario activo
    """
    usuario = db.query(Usuario).filter(Usuario.email == email).first()
    if not usuario:
        return False

    if not verificar_password(password, usuario.password_hash):
        return False

    # ✅ VALIDACIÓN 1: Email verificado
    if not getattr(usuario, "email_verificado", False):
        logger.warning(f"⚠️ Intento de login con email no verificado: {email}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Por favor verifica tu email antes de iniciar sesión."
        )

  
    if usuario.deleted_at is not None:
        logger.warning(f"⚠️ Intento de login de usuario eliminado: {email}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Tu cuenta ha sido deshabilitada. Contacta al administrador."
        )


    if not usuario.activo:
        logger.warning(f"⚠️ Intento de login de usuario inactivo: {email}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Tu cuenta está inactiva. Contacta al administrador."
        )


    if getattr(usuario, "bloqueado", False):
        logger.warning(f"⚠️ Intento de login de usuario bloqueado: {email}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Tu cuenta está bloqueada. Contacta al administrador."
        )


    usuario.ultimo_login = now_utc()
    db.commit()
    
    logger.info(f"✅ Login exitoso: {email}")
    return usuario




def crear_usuario(db: Session, usuario: UsuarioCreate):
    """
    Crea un nuevo usuario validando que el email no esté en uso
    (solo entre usuarios NO eliminados).
    """
    # Validar email único (solo usuarios NO eliminados)
    db_usuario = db.query(Usuario).filter(
        Usuario.email == usuario.email,
        Usuario.deleted_at.is_(None)  # ← Solo no eliminados
    ).first()
    
    if db_usuario:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El email ya está registrado"
        )

    token_verificacion = secrets.token_urlsafe(32)
    token_expira = now_utc() + timedelta(hours=24)

    hashed_password = obtener_password_hash(usuario.password)
    db_usuario = Usuario(
        email=usuario.email,
        password_hash=hashed_password,
        nombre=usuario.nombre,
        apellido=usuario.apellido,
        activo=usuario.activo,

        email_verificado=False,
        token_verificacion=token_verificacion,
        token_verificacion_expira=token_expira,
    )

    db.add(db_usuario)
    db.commit()
    db.refresh(db_usuario)

    logger.info(f"✅ Usuario creado: {db_usuario.email} (ID: {db_usuario.id})")

    try:
        email_enviado = email_service.send_verification_email(
            to_email=db_usuario.email,
            usuario_nombre=f"{db_usuario.nombre} {db_usuario.apellido}".strip(),
            verify_token=token_verificacion
        )
        if email_enviado:
            logger.info(f"📧 Email de verificación enviado a {db_usuario.email}")
        else:
            logger.warning(f"⚠️ No se pudo enviar email de verificación a {db_usuario.email}")
    except Exception as e:
        logger.exception(f"❌ Error al enviar email de verificación: {e}")

    return db_usuario




def verificar_email(db: Session, token: str):
    usuario = db.query(Usuario).filter(
        Usuario.token_verificacion == token,
        Usuario.token_verificacion_expira > now_utc()
    ).first()

    if not usuario:
        logger.warning("⚠️ Intento de verificación con token inválido o expirado")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Token de verificación inválido o expirado."
        )

    if usuario.email_verificado:
        logger.info(f"ℹ️ Email ya verificado anteriormente: {usuario.email}")
        return {"mensaje": "Email ya verificado anteriormente.", "email": usuario.email}

    usuario.email_verificado = True
    usuario.token_verificacion = None
    usuario.token_verificacion_expira = None
    db.commit()

    logger.info(f"✅ Email verificado exitosamente: {usuario.email} (ID: {usuario.id})")
    return {"mensaje": "Email verificado exitosamente.", "email": usuario.email}


def reenviar_verificacion(db: Session, email: str):
    # Buscar usuario NO eliminado
    usuario = db.query(Usuario).filter(
        Usuario.email == email,
        Usuario.deleted_at.is_(None) 
    ).first()

    if not usuario:
        logger.warning(f"⚠️ Reenvío a email no existente: {email}")
        raise HTTPException(status_code=404, detail="Usuario no encontrado.")

    if usuario.email_verificado:
        raise HTTPException(status_code=400, detail="Este email ya ha sido verificado.")

    token_verificacion = secrets.token_urlsafe(32)
    token_expira = now_utc() + timedelta(hours=24)

    usuario.token_verificacion = token_verificacion
    usuario.token_verificacion_expira = token_expira
    db.commit()

    try:
        email_enviado = email_service.send_verification_email(
            to_email=usuario.email,
            usuario_nombre=f"{usuario.nombre} {usuario.apellido}".strip(),
            verify_token=token_verificacion
        )
        if not email_enviado:
            raise Exception("Proveedor de email devolvió False")
    except Exception as e:
        logger.exception(f"❌ Error al reenviar verificación: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error al enviar el email de verificación."
        )

    return {"mensaje": "Email de verificación reenviado exitosamente.", "email": usuario.email}




def cambiar_password(db: Session, usuario_id: int, cambio: CambioPassword):
    usuario = db.query(Usuario).filter(Usuario.id == usuario_id).first()
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    if not verificar_password(cambio.password_actual, usuario.password_hash):
        raise HTTPException(status_code=400, detail="Contraseña actual incorrecta")

    usuario.password_hash = obtener_password_hash(cambio.nuevo_password)
    usuario.fecha_actualizacion = now_utc()

    db.commit()
    return {"mensaje": "Contraseña actualizada correctamente"}




def resetear_password(db: Session, email: str, ip_address: str = None):
    respuesta_ok = {
        "mensaje": "Si el email existe, se enviarán instrucciones para resetear la contraseña",
        "email": email
    }

    # Buscar usuario NO eliminado
    usuario = db.query(Usuario).filter(
        Usuario.email == email,
        Usuario.deleted_at.is_(None)  
    ).first()
    
    if not usuario:
        logger.info(f"🔐 Reset solicitado para email no existente: {email}")
        return respuesta_ok

    token_value = secrets.token_urlsafe(32)

    usuario.token_reset_password = token_value
    usuario.token_reset_expira = now_utc() + timedelta(hours=1)
    usuario.token_reset_usado = False
    usuario.token_reset_ip = ip_address

    try:
        db.commit()
    except SQLAlchemyError as e:
        db.rollback()
        logger.exception(f"❌ Error guardando token reset en usuario: {e}")
        return respuesta_ok

    try:
        email_service.send_reset_password_email(
            to_email=usuario.email,
            usuario_nombre=usuario.nombre or usuario.email.split("@")[0],
            reset_token=token_value
        )
    except Exception as e:
        logger.exception(f"❌ Error enviando email de reset: {e}")

    debug_mode = bool(getattr(settings, "DEBUG", False))
    if debug_mode:
        return {
            **respuesta_ok,
            "debug_token": token_value,
            "debug_expires": (usuario.token_reset_expira.isoformat() if usuario.token_reset_expira else None)
        }

    return respuesta_ok


def confirmar_reset_password(db: Session, token: str, nuevo_password: str):
    usuario = db.query(Usuario).filter(Usuario.token_reset_password == token).first()

    if not usuario:
        raise HTTPException(status_code=400, detail="Token de reset inválido o expirado")

    if getattr(usuario, "token_reset_usado", False):
        raise HTTPException(status_code=400, detail="Este token ya fue utilizado")

    expira = getattr(usuario, "token_reset_expira", None)

    if not expira or expira < now_utc():
        raise HTTPException(status_code=400, detail="El token de reset ha expirado. Solicita uno nuevo.")

    if len(nuevo_password) < 8:
        raise HTTPException(status_code=400, detail="La contraseña debe tener al menos 8 caracteres")

    usuario.password_hash = obtener_password_hash(nuevo_password)
    usuario.fecha_actualizacion = now_utc()

    usuario.token_reset_usado = True
    usuario.token_reset_password = None
    usuario.token_reset_expira = None
    usuario.token_reset_ip = None

    try:
        db.commit()
    except SQLAlchemyError as e:
        db.rollback()
        logger.exception(f"❌ Error al confirmar reset: {e}")
        raise HTTPException(status_code=500, detail="Error al procesar el reset de contraseña")

    return {
        "mensaje": "Contraseña restablecida correctamente. Ya puedes iniciar sesión con tu nueva contraseña.",
        "email": usuario.email
    }

def configurar_cuenta_docente(db: Session, token: str, nuevo_password: str):
    if not nuevo_password or len(nuevo_password) < 6:
        raise HTTPException(status_code=400, detail="La contraseña debe tener al menos 6 caracteres")

    usuario = db.query(Usuario).filter(
        Usuario.token_reset_password == token,
        Usuario.token_reset_expira > now_utc(),
        Usuario.token_reset_usado == False,
        Usuario.deleted_at.is_(None)
    ).first()

    if not usuario:
        raise HTTPException(status_code=400, detail="Token inválido o expirado")

    usuario.password_hash = obtener_password_hash(nuevo_password)
    usuario.email_verificado = True

    usuario.token_reset_usado = True
    usuario.token_reset_password = None
    usuario.token_reset_expira = None

    usuario.fecha_actualizacion = now_utc()
    db.commit()

    return {"mensaje": "Cuenta configurada correctamente. Ya puedes iniciar sesión.", "email": usuario.email}
