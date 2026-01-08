from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import timedelta

from app.config import get_db
from app.modelos import Usuario, UsuarioRol, Padre
from app.esquemas.auth import (
    Token,
    UsuarioCreate,
    UsuarioResponse,
    CambioPassword,
    ResetPasswordRequest,
    ResetPasswordConfirm
)

from app.servicios.auth import (
    autenticar_usuario,
    crear_usuario,
    cambiar_password,
    resetear_password,
    confirmar_reset_password
)

from app.servicios.seguridad import (
    obtener_usuario_actual,
    crear_token_acceso,   # ✅ ESTA ERA LA CLAVE
    asignar_rol
)

router = APIRouter(prefix="/auth", tags=["autenticacion"])

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

# ============================
# REGISTRO
# ============================
@router.post("/registro", response_model=UsuarioResponse)
def registro(usuario: UsuarioCreate, db: Session = Depends(get_db)):
    return crear_usuario(db, usuario)

# ============================
# LOGIN
# ============================
@router.post("/login", response_model=Token)
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    usuario = autenticar_usuario(db, form_data.username, form_data.password)
    if not usuario:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciales incorrectas",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token_expires = timedelta(minutes=30)
    access_token = crear_token_acceso(
        data={"sub": usuario.email, "id": usuario.id},
        expires_delta=access_token_expires
    )

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "expires_in": int(access_token_expires.total_seconds())
    }

# ============================
# CAMBIO PASSWORD
# ============================
@router.post("/cambio-password")
def cambio_password_endpoint(
    cambio: CambioPassword,
    db: Session = Depends(get_db),
    usuario_actual: Usuario = Depends(obtener_usuario_actual)
):
    return cambiar_password(db, usuario_actual.id, cambio)

# ============================
# RESET PASSWORD
# ============================
@router.post("/reset-password")
def reset_password(
    request: ResetPasswordRequest,
    req: Request,
    db: Session = Depends(get_db)
):
    """
    Solicita un token de reset de contraseña.

    El token se genera y guarda en la BD con expiración de 1 hora.
    En producción, se enviaría por email al usuario.

    Por seguridad, siempre retorna el mismo mensaje independientemente
    de si el email existe o no.

    Args:
        request: Objeto con el email del usuario
        req: Request object (para obtener IP)
        db: Sesión de base de datos

    Returns:
        dict: Mensaje genérico + token en modo debug
    """
    # Obtener IP del cliente
    ip_address = None
    if hasattr(req, 'client') and req.client:
        ip_address = req.client.host
    elif 'x-forwarded-for' in req.headers:
        ip_address = req.headers['x-forwarded-for'].split(',')[0].strip()
    elif 'x-real-ip' in req.headers:
        ip_address = req.headers['x-real-ip']

    return resetear_password(db, request.email, ip_address)


@router.post("/confirm-reset-password")
def confirm_reset_password(
    request: ResetPasswordConfirm,
    db: Session = Depends(get_db)
):
    """
    Confirma el reset de contraseña usando el token recibido.

    El token debe ser válido, no usado y no expirado.
    Si es válido, cambia la contraseña del usuario.

    Args:
        request: Objeto con token y nueva contraseña
        db: Sesión de base de datos

    Returns:
        dict: Mensaje de éxito

    Raises:
        HTTPException 400: Si el token es inválido, usado o expirado
        HTTPException 400: Si la contraseña no cumple requisitos
    """
    return confirmar_reset_password(db, request.token, request.nuevo_password)

# ============================
# USUARIO ACTUAL
# ============================
@router.get("/me", response_model=UsuarioResponse)
def me(
    db: Session = Depends(get_db),
    usuario_actual: Usuario = Depends(obtener_usuario_actual),
):
    roles_rows = (
        db.query(UsuarioRol.rol)
        .filter(
            UsuarioRol.usuario_id == usuario_actual.id,
            UsuarioRol.activo == True,
        )
        .all()
    )

    roles = [r[0] for r in roles_rows]

    return UsuarioResponse(
        id=usuario_actual.id,
        email=usuario_actual.email,
        nombre=usuario_actual.nombre,
        apellido=usuario_actual.apellido,
        activo=usuario_actual.activo,
        fecha_creacion=usuario_actual.fecha_creacion,
        ultimo_login=usuario_actual.ultimo_login,
        bloqueado=usuario_actual.bloqueado,
        roles=roles,
    )

# ============================
# REGISTRO PADRE
# ============================
@router.post("/registro-padre", response_model=UsuarioResponse)
def registro_padre(datos: UsuarioCreate, db: Session = Depends(get_db)):
    nuevo_usuario = crear_usuario(db, datos)

    asignar_rol(db, nuevo_usuario.id, "padre")

    nuevo_padre = Padre(
        usuario_id=nuevo_usuario.id,
        parentesco="padre",
        notificaciones_activas=True
    )

    db.add(nuevo_padre)
    db.commit()
    db.refresh(nuevo_padre)

    return nuevo_usuario
