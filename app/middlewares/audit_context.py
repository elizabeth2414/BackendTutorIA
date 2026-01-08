"""
Middleware de Contexto de Auditoría

Este módulo proporciona una dependency mejorada para configurar el contexto
del usuario autenticado en la sesión de PostgreSQL, permitiendo que los
triggers de auditoría capturen automáticamente el usuario_id.

PROBLEMA ANTERIOR:
- Los triggers guardaban usuario_id = NULL porque no tenían contexto
- No se podía saber quién hizo cada cambio en la auditoría

SOLUCIÓN:
- Usar variables de sesión de PostgreSQL (SET LOCAL)
- Los triggers leen esas variables para obtener el usuario_id
- Automático y transparente para el código

USO:
    # En lugar de usar get_db directamente:
    from app.middlewares import get_db_with_audit_context

    @router.post("/recursos")
    def crear_recurso(
        db: Session = Depends(get_db_with_audit_context),
        usuario_actual: Usuario = Depends(obtener_usuario_actual)
    ):
        # El contexto ya está configurado automáticamente
        # Los triggers guardarán usuario_id correctamente
        ...
"""

from typing import Optional, Generator
from fastapi import Depends, Request
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.config import get_db
from app.servicios.seguridad import obtener_usuario_actual
from app.modelos import Usuario
from app.logs.logger import logger


def set_audit_context(db: Session, usuario_id: Optional[int], ip_address: Optional[str] = None):
    """
    Configura el contexto de auditoría en la sesión de PostgreSQL.

    Establece variables de sesión que los triggers pueden leer:
    - app.current_user_id: ID del usuario autenticado
    - app.current_user_ip: IP del usuario (opcional)

    Args:
        db: Sesión de SQLAlchemy
        usuario_id: ID del usuario autenticado (puede ser None para endpoints públicos)
        ip_address: Dirección IP del usuario (opcional)
    """
    try:
        if usuario_id is not None:
            # Configurar usuario_id en la sesión de PostgreSQL
            db.execute(text("SET LOCAL app.current_user_id = :user_id"), {"user_id": usuario_id})
            logger.debug(f"🔐 Contexto de auditoría configurado: usuario_id={usuario_id}")
        else:
            # Para endpoints públicos, limpiar el contexto
            db.execute(text("SET LOCAL app.current_user_id = NULL"))
            logger.debug("🔓 Contexto de auditoría: usuario público (sin autenticación)")

        if ip_address:
            db.execute(text("SET LOCAL app.current_user_ip = :ip"), {"ip": ip_address})
            logger.debug(f"🌐 IP configurada en contexto: {ip_address}")

    except Exception as e:
        # No fallar si hay error al configurar contexto
        # Los triggers deberían manejar el caso de variables no definidas
        logger.warning(f"⚠️ No se pudo configurar contexto de auditoría: {str(e)}")


def get_db_with_audit_context(
    request: Request,
    usuario_actual: Usuario = Depends(obtener_usuario_actual),
    db: Session = Depends(get_db)
) -> Generator[Session, None, None]:
    """
    Dependency mejorada que configura el contexto de auditoría automáticamente.

    Usa esta dependency en lugar de get_db cuando necesites que los triggers
    de auditoría capturen el usuario_id correctamente.

    Características:
    - Configura usuario_id del usuario autenticado
    - Configura IP del cliente (extraída del request)
    - Transparente para el código del endpoint
    - Compatible con todos los routers existentes

    Args:
        request: Request de FastAPI (para obtener IP)
        usuario_actual: Usuario autenticado (inyectado automáticamente)
        db: Sesión de base de datos (inyectada automáticamente)

    Yields:
        Session: Sesión de SQLAlchemy con contexto configurado

    Example:
        @router.post("/estudiantes")
        def crear_estudiante(
            estudiante: EstudianteCreate,
            db: Session = Depends(get_db_with_audit_context),
            usuario_actual: Usuario = Depends(obtener_usuario_actual)
        ):
            # Los triggers de auditoría automáticamente guardarán
            # usuario_id = usuario_actual.id
            nuevo = Estudiante(**estudiante.dict())
            db.add(nuevo)
            db.commit()
            return nuevo
    """

    # Obtener IP del cliente
    ip_address = None
    if hasattr(request, 'client') and request.client:
        ip_address = request.client.host
    elif 'x-forwarded-for' in request.headers:
        # Si está detrás de un proxy/load balancer
        ip_address = request.headers['x-forwarded-for'].split(',')[0].strip()
    elif 'x-real-ip' in request.headers:
        ip_address = request.headers['x-real-ip']

    # Configurar contexto de auditoría
    set_audit_context(
        db=db,
        usuario_id=usuario_actual.id if usuario_actual else None,
        ip_address=ip_address
    )

    try:
        yield db
    finally:
        # Limpiar el contexto al finalizar
        # (SET LOCAL se limpia automáticamente al final de la transacción,
        # pero es buena práctica hacerlo explícito)
        try:
            db.execute(text("RESET app.current_user_id"))
            db.execute(text("RESET app.current_user_ip"))
        except Exception:
            # Ignorar errores al limpiar (la sesión puede estar cerrada)
            pass


def get_db_with_audit_context_optional(
    request: Request,
    db: Session = Depends(get_db)
) -> Generator[Session, None, None]:
    """
    Dependency para endpoints que NO requieren autenticación pero queremos
    auditar de todas formas.

    Similar a get_db_with_audit_context pero sin requerir usuario autenticado.
    Útil para endpoints públicos como registro, login, etc.

    Args:
        request: Request de FastAPI (para obtener IP)
        db: Sesión de base de datos

    Yields:
        Session: Sesión con contexto configurado (usuario_id = NULL)

    Example:
        @router.post("/auth/register")
        def registrar_usuario(
            datos: RegistroUsuario,
            db: Session = Depends(get_db_with_audit_context_optional)
        ):
            # Los triggers guardarán usuario_id = NULL (usuario público)
            # pero sí capturarán la IP y otros datos
            ...
    """

    # Obtener IP del cliente
    ip_address = None
    if hasattr(request, 'client') and request.client:
        ip_address = request.client.host
    elif 'x-forwarded-for' in request.headers:
        ip_address = request.headers['x-forwarded-for'].split(',')[0].strip()
    elif 'x-real-ip' in request.headers:
        ip_address = request.headers['x-real-ip']

    # Configurar contexto sin usuario (NULL)
    set_audit_context(
        db=db,
        usuario_id=None,
        ip_address=ip_address
    )

    try:
        yield db
    finally:
        try:
            db.execute(text("RESET app.current_user_id"))
            db.execute(text("RESET app.current_user_ip"))
        except Exception:
            pass


# ============================================
# FUNCIONES AUXILIARES PARA USO MANUAL
# ============================================

def configurar_contexto_auditoria_manual(
    db: Session,
    usuario_id: int,
    ip_address: Optional[str] = None
):
    """
    Configura manualmente el contexto de auditoría.

    Úsala solo cuando NO puedas usar las dependencies (ej: operaciones batch,
    scripts de migración, tareas asíncronas, etc.)

    Args:
        db: Sesión de SQLAlchemy
        usuario_id: ID del usuario que ejecuta la operación
        ip_address: IP del usuario (opcional)

    Example:
        # En un script de migración
        db = SessionLocal()
        configurar_contexto_auditoria_manual(db, usuario_id=1, ip_address="127.0.0.1")

        # Hacer operaciones...
        estudiante = Estudiante(nombre="Juan")
        db.add(estudiante)
        db.commit()

        # Los triggers guardarán usuario_id = 1
    """
    set_audit_context(db, usuario_id, ip_address)


def limpiar_contexto_auditoria(db: Session):
    """
    Limpia el contexto de auditoría de la sesión.

    Úsala al finalizar operaciones manuales que configuraron el contexto.

    Args:
        db: Sesión de SQLAlchemy
    """
    try:
        db.execute(text("RESET app.current_user_id"))
        db.execute(text("RESET app.current_user_ip"))
        logger.debug("🧹 Contexto de auditoría limpiado")
    except Exception as e:
        logger.warning(f"⚠️ Error al limpiar contexto: {str(e)}")
