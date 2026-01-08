# app/servicios/seguridad.py

from datetime import datetime, timedelta
from typing import Optional

from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import HTTPException, status, Depends
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app import settings
from app.config import get_db
from app.modelos import Usuario, UsuarioRol, Docente 

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Ojo: este tokenUrl es el endpoint de login que ya tienes definido.
# Si tu router de auth está con prefix="/auth" y lo incluyes con prefix="/api",
# el endpoint real será /api/auth/login, pero aquí puede quedar "auth/login"
# porque solo se usa para la documentación de OpenAPI.
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")


# ==============================
# HASH / VERIFICACIÓN DE PASSWORD
# ==============================

def verificar_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def obtener_password_hash(password: str) -> str:
    return pwd_context.hash(password)


# Alias para reutilizar en otros módulos (como docente_admin.py)
def get_password_hash(password: str) -> str:
    return obtener_password_hash(password)


# ==============================
# MANEJO DE TOKENS JWT
# ==============================

def crear_token_acceso(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        # Por defecto 15 minutos
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})

    encoded_jwt = jwt.encode(
        to_encode,
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM
    )
    return encoded_jwt


def verificar_token_acceso(token: str):
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM]
        )
        return payload
    except JWTError:
        return None


# ==============================
# OBTENER USUARIO ACTUAL
# ==============================

async def obtener_usuario_actual(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="No se pudieron validar las credenciales",
        headers={"WWW-Authenticate": "Bearer"},
    )

    payload = verificar_token_acceso(token)
    if payload is None:
        raise credentials_exception

    email: str = payload.get("sub")
    if email is None:
        raise credentials_exception

    usuario = db.query(Usuario).filter(Usuario.email == email).first()
    if usuario is None:
        raise credentials_exception

    return usuario


# ==============================
# VALIDACIÓN DE ROLES
# ==============================

from app.logs.logger import logger
from typing import List


def verificar_rol(
    db: Session,
    usuario_id: int,
    rol_requerido: str,
    verificar_activo: bool = True
) -> bool:
    """
    Función auxiliar que verifica si un usuario tiene un rol específico.

    Args:
        db: Sesión de base de datos
        usuario_id: ID del usuario a verificar
        rol_requerido: Rol a verificar ('admin', 'docente', 'estudiante', 'padre')
        verificar_activo: Si True, solo considera roles activos

    Returns:
        bool: True si el usuario tiene el rol, False en caso contrario
    """
    query = db.query(UsuarioRol).filter(
        UsuarioRol.usuario_id == usuario_id,
        UsuarioRol.rol == rol_requerido.lower()
    )

    if verificar_activo:
        query = query.filter(UsuarioRol.activo == True)

    rol = query.first()
    return rol is not None


def obtener_roles_usuario(
    db: Session,
    usuario_id: int,
    solo_activos: bool = True
) -> List[str]:
    """
    Obtiene todos los roles de un usuario.

    Args:
        db: Sesión de base de datos
        usuario_id: ID del usuario
        solo_activos: Si True, solo retorna roles activos

    Returns:
        List[str]: Lista de roles del usuario (ej: ['admin', 'docente'])
    """
    query = db.query(UsuarioRol.rol).filter(
        UsuarioRol.usuario_id == usuario_id
    )

    if solo_activos:
        query = query.filter(UsuarioRol.activo == True)

    roles = query.all()
    return [rol[0] for rol in roles]


# ==============================
# DEPENDENCIES DE VALIDACIÓN DE ROLES
# ==============================

def requiere_admin(
    usuario: Usuario = Depends(obtener_usuario_actual),
    db: Session = Depends(get_db)
) -> Usuario:
    """
    Dependency que verifica que el usuario autenticado tenga rol 'admin'.

    Uso:
        @router.post("/admin/recurso")
        def crear_recurso(
            admin: Usuario = Depends(requiere_admin)
        ):
            # Solo usuarios con rol admin pueden acceder
            ...

    Args:
        usuario: Usuario autenticado (inyectado automáticamente)
        db: Sesión de base de datos (inyectada automáticamente)

    Returns:
        Usuario: El usuario autenticado con rol admin

    Raises:
        HTTPException 403: Si el usuario no tiene rol admin
    """
    tiene_rol = verificar_rol(db, usuario.id, "admin")

    if not tiene_rol:
        logger.warning(
            f"⚠️ Acceso denegado: {usuario.email} intentó acceder a endpoint admin sin permisos"
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acceso denegado: se requiere rol de administrador"
        )

    logger.debug(f"✅ Acceso admin autorizado: {usuario.email}")
    return usuario

def requiere_docente(
    usuario: Usuario = Depends(obtener_usuario_actual),
    db: Session = Depends(get_db)
) -> Usuario:
    """
    Dependency que verifica que el usuario autenticado tenga rol 'docente'.

    Uso:
        @router.get("/docentes/mis-cursos")
        def obtener_mis_cursos(
            docente: Usuario = Depends(requiere_docente)
        ):
            # Solo docentes pueden acceder
            ...

    Args:
        usuario: Usuario autenticado (inyectado automáticamente)
        db: Sesión de base de datos (inyectada automáticamente)

    Returns:
        Usuario: El usuario autenticado con rol docente

    Raises:
        HTTPException 403: Si el usuario no tiene rol docente
    """
    tiene_rol = verificar_rol(db, usuario.id, "docente")

    if not tiene_rol:
        logger.warning(
            f"⚠️ Acceso denegado: {usuario.email} intentó acceder a endpoint docente sin permisos"
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acceso denegado: se requiere rol de docente"
        )

    logger.debug(f"✅ Acceso docente autorizado: {usuario.email}")
    return usuario


def requiere_estudiante(
    usuario: Usuario = Depends(obtener_usuario_actual),
    db: Session = Depends(get_db)
) -> Usuario:
    """
    Dependency que verifica que el usuario autenticado tenga rol 'estudiante'.

    Uso:
        @router.get("/estudiantes/mi-progreso")
        def obtener_mi_progreso(
            estudiante: Usuario = Depends(requiere_estudiante)
        ):
            # Solo estudiantes pueden acceder
            ...

    Args:
        usuario: Usuario autenticado (inyectado automáticamente)
        db: Sesión de base de datos (inyectada automáticamente)

    Returns:
        Usuario: El usuario autenticado con rol estudiante

    Raises:
        HTTPException 403: Si el usuario no tiene rol estudiante
    """
    tiene_rol = verificar_rol(db, usuario.id, "estudiante")

    if not tiene_rol:
        logger.warning(
            f"⚠️ Acceso denegado: {usuario.email} intentó acceder a endpoint estudiante sin permisos"
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acceso denegado: se requiere rol de estudiante"
        )

    logger.debug(f"✅ Acceso estudiante autorizado: {usuario.email}")
    return usuario


def requiere_padre(
    usuario: Usuario = Depends(obtener_usuario_actual),
    db: Session = Depends(get_db)
) -> Usuario:
    """
    Dependency que verifica que el usuario autenticado tenga rol 'padre'.

    Uso:
        @router.get("/padres/mis-hijos")
        def obtener_mis_hijos(
            padre: Usuario = Depends(requiere_padre)
        ):
            # Solo padres pueden acceder
            ...

    Args:
        usuario: Usuario autenticado (inyectado automáticamente)
        db: Sesión de base de datos (inyectada automáticamente)

    Returns:
        Usuario: El usuario autenticado con rol padre

    Raises:
        HTTPException 403: Si el usuario no tiene rol padre
    """
    tiene_rol = verificar_rol(db, usuario.id, "padre")

    if not tiene_rol:
        logger.warning(
            f"⚠️ Acceso denegado: {usuario.email} intentó acceder a endpoint padre sin permisos"
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acceso denegado: se requiere rol de padre/tutor"
        )

    logger.debug(f"✅ Acceso padre autorizado: {usuario.email}")
    return usuario


def requiere_cualquier_rol(*roles_permitidos: str):
    """
    Factory function que crea una dependency que verifica múltiples roles.

    El usuario debe tener AL MENOS UNO de los roles especificados.

    Uso:
        @router.get("/recursos/compartidos")
        def obtener_recursos_compartidos(
            usuario: Usuario = Depends(requiere_cualquier_rol("admin", "docente"))
        ):
            # Administradores O docentes pueden acceder
            ...

    Args:
        *roles_permitidos: Roles permitidos (ej: "admin", "docente", "estudiante")

    Returns:
        Callable: Dependency function que verifica los roles

    Example:
        # Permitir admin O docente
        @router.post("/contenido")
        def crear_contenido(
            usuario: Usuario = Depends(requiere_cualquier_rol("admin", "docente"))
        ):
            ...

        # Permitir admin O docente O padre
        @router.get("/estudiantes/{id}/progreso")
        def ver_progreso(
            estudiante_id: int,
            usuario: Usuario = Depends(requiere_cualquier_rol("admin", "docente", "padre"))
        ):
            ...
    """
    def dependency(
        usuario: Usuario = Depends(obtener_usuario_actual),
        db: Session = Depends(get_db)
    ) -> Usuario:
        # Obtener todos los roles del usuario
        roles_usuario = obtener_roles_usuario(db, usuario.id)

        # Verificar si tiene al menos uno de los roles permitidos
        roles_permitidos_lower = [r.lower() for r in roles_permitidos]
        tiene_acceso = any(rol in roles_permitidos_lower for rol in roles_usuario)

        if not tiene_acceso:
            roles_str = ", ".join(roles_permitidos)
            logger.warning(
                f"⚠️ Acceso denegado: {usuario.email} intentó acceder sin roles requeridos. "
                f"Tiene: {roles_usuario}, Necesita: [{roles_str}]"
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Acceso denegado: se requiere uno de los siguientes roles: {roles_str}"
            )

        logger.debug(f"✅ Acceso autorizado: {usuario.email} con roles {roles_usuario}")
        return usuario

    return dependency


def requiere_todos_los_roles(*roles_requeridos: str):
    """
    Factory function que crea una dependency que verifica múltiples roles.

    El usuario debe tener TODOS los roles especificados.

    Uso:
        @router.get("/admin/docentes/estadisticas")
        def estadisticas_avanzadas(
            usuario: Usuario = Depends(requiere_todos_los_roles("admin", "docente"))
        ):
            # Solo usuarios que son TANTO admin COMO docente pueden acceder
            ...

    Args:
        *roles_requeridos: Roles requeridos (todos deben estar presentes)

    Returns:
        Callable: Dependency function que verifica los roles

    Example:
        # Requiere tener ambos roles
        @router.post("/cursos/especiales")
        def crear_curso_especial(
            usuario: Usuario = Depends(requiere_todos_los_roles("admin", "docente"))
        ):
            # El usuario debe ser admin Y docente
            ...
    """
    def dependency(
        usuario: Usuario = Depends(obtener_usuario_actual),
        db: Session = Depends(get_db)
    ) -> Usuario:
        # Obtener todos los roles del usuario
        roles_usuario = obtener_roles_usuario(db, usuario.id)

        # Verificar si tiene TODOS los roles requeridos
        roles_requeridos_lower = [r.lower() for r in roles_requeridos]
        tiene_todos = all(rol in roles_usuario for rol in roles_requeridos_lower)

        if not tiene_todos:
            roles_str = ", ".join(roles_requeridos)
            faltantes = [r for r in roles_requeridos_lower if r not in roles_usuario]
            logger.warning(
                f"⚠️ Acceso denegado: {usuario.email} no tiene todos los roles requeridos. "
                f"Tiene: {roles_usuario}, Faltan: {faltantes}"
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Acceso denegado: se requieren TODOS los siguientes roles: {roles_str}"
            )

        logger.debug(f"✅ Acceso autorizado: {usuario.email} tiene todos los roles requeridos")
        return usuario

    return dependency

def asignar_rol(db: Session, usuario_id: int, rol: str):
    rol = rol.lower()  # 👈 IMPORTANTE

    from app.modelos import UsuarioRol

    rol_existente = (
        db.query(UsuarioRol)
        .filter(
            UsuarioRol.usuario_id == usuario_id,
            UsuarioRol.rol == rol
        )
        .first()
    )

    if rol_existente:
        rol_existente.activo = True
        db.commit()
        db.refresh(rol_existente)
        return rol_existente

    nuevo_rol = UsuarioRol(
        usuario_id=usuario_id,
        rol=rol,    # 👈 YA ESTÁ EN MINÚSCULA
        activo=True
    )

    db.add(nuevo_rol)
    db.commit()
    db.refresh(nuevo_rol)

    return nuevo_rol

def obtener_docente_actual(
    usuario: Usuario = Depends(requiere_docente),
    db: Session = Depends(get_db)
) -> Docente:
    """
    Obtiene el objeto Docente asociado al usuario autenticado.
    
    Uso:
        @router.post("/lecturas")
        def crear_lectura(
            docente: Docente = Depends(obtener_docente_actual)
        ):
            # docente.id es el ID correcto de la tabla docente
            ...
    """
    docente = db.query(Docente).filter(Docente.usuario_id == usuario.id).first()
    
    if not docente:
        logger.error(f"❌ Usuario {usuario.email} tiene rol docente pero no registro en tabla docente")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error: usuario docente sin registro asociado"
        )
    
    logger.debug(f"✅ Docente obtenido: id={docente.id}, usuario_id={docente.usuario_id}")
    return docente
