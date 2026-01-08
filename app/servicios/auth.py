from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from datetime import datetime, timedelta
import secrets

from app import settings
from app.modelos import Usuario, UsuarioRol, PasswordResetToken
from app.esquemas.auth import UsuarioCreate, CambioPassword
from app.servicios.seguridad import (
    verificar_password, obtener_password_hash
)
from app.servicios.email_service import email_service
from app.logs.logger import logger


def autenticar_usuario(db: Session, email: str, password: str):
    usuario = db.query(Usuario).filter(Usuario.email == email).first()
    if not usuario:
        return False
    if not verificar_password(password, usuario.password_hash):
        return False
    return usuario

def crear_usuario(db: Session, usuario: UsuarioCreate):
    # Verificar si el usuario ya existe
    db_usuario = db.query(Usuario).filter(Usuario.email == usuario.email).first()
    if db_usuario:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El email ya está registrado"
        )

    # Crear usuario
    hashed_password = obtener_password_hash(usuario.password)
    db_usuario = Usuario(
        email=usuario.email,
        password_hash=hashed_password,
        nombre=usuario.nombre,
        apellido=usuario.apellido,
        activo=usuario.activo
    )
    db.add(db_usuario)
    db.commit()
    db.refresh(db_usuario)
    return db_usuario

def cambiar_password(db: Session, usuario_id: int, cambio: CambioPassword):
    usuario = db.query(Usuario).filter(Usuario.id == usuario_id).first()
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    # Verificar contraseña actual
    if not verificar_password(cambio.password_actual, usuario.password_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Contraseña actual incorrecta"
        )

    # Actualizar contraseña
    usuario.password_hash = obtener_password_hash(cambio.nuevo_password)
    db.commit()
    return {"mensaje": "Contraseña actualizada correctamente"}


# ============================================
# FUNCIONALIDAD DE RESET PASSWORD
# ============================================

def resetear_password(db: Session, email: str, ip_address: str = None):
    """
    Genera un token de reset de contraseña para el usuario.

    Por seguridad, siempre retorna el mismo mensaje independientemente
    de si el email existe o no.

    Args:
        db: Sesión de base de datos
        email: Email del usuario que solicita el reset
        ip_address: IP del solicitante (opcional, para seguridad)

    Returns:
        dict: Mensaje genérico de éxito

    Proceso:
        1. Busca el usuario por email
        2. Si existe:
           - Invalida tokens anteriores no usados
           - Genera token seguro de 32 bytes
           - Guarda en BD con expiración de 1 hora
           - (Aquí se enviaría email con el token)
        3. Si NO existe:
           - No hace nada (por seguridad)
        4. Siempre retorna el mismo mensaje
    """
    usuario = db.query(Usuario).filter(Usuario.email == email).first()

    if not usuario:
        # Por seguridad, no revelamos si el email existe
        logger.info(f"🔐 Intento de reset password para email no existente: {email}")
        return {
            "mensaje": "Si el email existe, se enviarán instrucciones para resetear la contraseña",
            "email": email
        }

    # Usuario existe, generar token
    logger.info(f"🔐 Solicitud de reset password para: {usuario.email} (ID: {usuario.id})")

    # 1. Invalidar tokens anteriores no usados
    tokens_anteriores = db.query(PasswordResetToken).filter(
        PasswordResetToken.usuario_id == usuario.id,
        PasswordResetToken.usado == False,
        PasswordResetToken.fecha_expiracion > datetime.utcnow()
    ).all()

    for token_anterior in tokens_anteriores:
        token_anterior.usado = True
        logger.debug(f"🗑️ Token anterior invalidado para usuario {usuario.id}")

    # 2. Generar nuevo token seguro
    token_value = secrets.token_urlsafe(32)  # 43 caracteres, URL-safe

    # 3. Crear registro en BD
    reset_token = PasswordResetToken(
        usuario_id=usuario.id,
        token=token_value,
        fecha_expiracion=datetime.utcnow() + timedelta(hours=1),
        usado=False,
        ip_solicitante=ip_address
    )

    db.add(reset_token)
    db.commit()

    logger.info(
        f"✅ Token de reset generado para {usuario.email}. "
        f"Expira en 1 hora. IP: {ip_address or 'N/A'}"
    )

    # 4. Enviar email con el token
    try:
        email_enviado = email_service.send_reset_password_email(
            to_email=usuario.email,
            usuario_nombre=usuario.nombre or usuario.email.split('@')[0],
            reset_token=token_value
        )

        if email_enviado:
            logger.info(f"📧 Email de reset enviado exitosamente a {usuario.email}")
        else:
            logger.warning(f"⚠️ No se pudo enviar email de reset a {usuario.email}")
    except Exception as e:
        logger.error(f"❌ Error al enviar email de reset a {usuario.email}: {str(e)}")
        # No lanzamos excepción para no revelar si el email existe

    debug_mode = getattr(settings, 'DEBUG', False)

    if debug_mode:
        # Solo en modo desarrollo
        logger.warning(f"⚠️ [DEBUG MODE] Token generado: {token_value}")
        return {
            "mensaje": "Si el email existe, se enviarán instrucciones para resetear la contraseña",
            "email": email,
            "debug_token": token_value,  # ⚠️ SOLO PARA DESARROLLO
            "debug_expires": reset_token.fecha_expiracion.isoformat()
        }

    # Respuesta normal en producción
    return {
        "mensaje": "Si el email existe, se enviarán instrucciones para resetear la contraseña",
        "email": email
    }


def confirmar_reset_password(db: Session, token: str, nuevo_password: str):
    """
    Verifica el token de reset y cambia la contraseña del usuario.

    Args:
        db: Sesión de base de datos
        token: Token de reset (recibido por email)
        nuevo_password: Nueva contraseña en texto plano (se hasheará)

    Returns:
        dict: Mensaje de éxito

    Raises:
        HTTPException 400: Si el token es inválido, expirado o ya usado
        HTTPException 400: Si la contraseña no cumple requisitos

    Proceso:
        1. Busca el token en la BD
        2. Valida que no esté usado
        3. Valida que no esté expirado
        4. Hashea la nueva contraseña
        5. Actualiza el usuario
        6. Marca el token como usado
        7. Invalida otros tokens del usuario
    """

    # 1. Buscar el token en la BD
    reset_token = db.query(PasswordResetToken).filter(
        PasswordResetToken.token == token
    ).first()

    if not reset_token:
        logger.warning(f"⚠️ Intento de usar token inválido de reset password")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Token de reset inválido o expirado"
        )

    # 2. Verificar que el token NO esté usado
    if reset_token.usado:
        logger.warning(
            f"⚠️ Intento de reusar token de reset ya usado. "
            f"Usuario ID: {reset_token.usuario_id}, Token usado en: {reset_token.fecha_uso}"
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Este token de reset ya fue utilizado"
        )

    # 3. Verificar que el token NO esté expirado
    if reset_token.fecha_expiracion < datetime.utcnow():
        tiempo_expirado = datetime.utcnow() - reset_token.fecha_expiracion
        logger.warning(
            f"⚠️ Intento de usar token expirado. "
            f"Usuario ID: {reset_token.usuario_id}, "
            f"Expiró hace: {tiempo_expirado}"
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El token de reset ha expirado. Solicita uno nuevo."
        )

    # 4. Validar la nueva contraseña (requisitos mínimos)
    if len(nuevo_password) < 8:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="La contraseña debe tener al menos 8 caracteres"
        )

    # 5. Obtener el usuario
    usuario = db.query(Usuario).filter(Usuario.id == reset_token.usuario_id).first()

    if not usuario:
        logger.error(
            f"❌ Token de reset apunta a usuario inexistente. "
            f"Token ID: {reset_token.id}, Usuario ID: {reset_token.usuario_id}"
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Usuario no encontrado"
        )

    # 6. Hashear la nueva contraseña
    nuevo_password_hash = obtener_password_hash(nuevo_password)

    # 7. Actualizar la contraseña del usuario
    usuario.password_hash = nuevo_password_hash
    usuario.fecha_actualizacion = datetime.utcnow()

    # 8. Marcar el token como usado
    reset_token.usado = True
    reset_token.fecha_uso = datetime.utcnow()

    # 9. Invalidar TODOS los otros tokens de reset del usuario
    otros_tokens = db.query(PasswordResetToken).filter(
        PasswordResetToken.usuario_id == usuario.id,
        PasswordResetToken.id != reset_token.id,
        PasswordResetToken.usado == False
    ).all()

    for otro_token in otros_tokens:
        otro_token.usado = True

    # 10. Commit de todos los cambios
    try:
        db.commit()

        logger.info(
            f"✅ Contraseña restablecida exitosamente para usuario: {usuario.email} (ID: {usuario.id})"
        )

        return {
            "mensaje": "Contraseña restablecida correctamente. Ya puedes iniciar sesión con tu nueva contraseña.",
            "email": usuario.email
        }

    except Exception as e:
        db.rollback()
        logger.error(f"❌ Error al resetear contraseña: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error al procesar el reset de contraseña"
        )
