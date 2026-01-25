from fastapi import APIRouter, Depends, HTTPException, status, Request, Query
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import timedelta
from pydantic import BaseModel, EmailStr

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
    confirmar_reset_password,
    verificar_email,          # ✅ NUEVO
    reenviar_verificacion     # ✅ NUEVO
)

from app.servicios.seguridad import (
    obtener_usuario_actual,
    crear_token_acceso,
    asignar_rol
)

router = APIRouter(prefix="/auth", tags=["autenticacion"])

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")


# ============================
# SCHEMA NUEVO (si no lo tienes en esquemas)
# ============================
class ReenviarVerificacionRequest(BaseModel):
    email: EmailStr


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
    # ⚠️ OJO: autenticar_usuario ahora puede lanzar HTTPException 403
    # si el email no está verificado. Eso está bien: FastAPI lo devolverá.
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
# VERIFICAR EMAIL (NUEVO)
# Link típico: /auth/verificar-email?token=xxxxx
# ============================
@router.get("/verificar-email")
def verificar_email_endpoint(
    token: str = Query(..., min_length=10),
    db: Session = Depends(get_db)
):
    return verificar_email(db, token)


# ============================
# REENVIAR VERIFICACIÓN (NUEVO)
# ============================
@router.post("/reenviar-verificacion")
def reenviar_verificacion_endpoint(
    request: ReenviarVerificacionRequest,
    db: Session = Depends(get_db)
):
    return reenviar_verificacion(db, request.email)


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
def confirm_reset_password_endpoint(
    request: ResetPasswordConfirm,
    db: Session = Depends(get_db)
):
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
    # 1) Si ya existe usuario, NO crearlo de nuevo
    usuario = db.query(Usuario).filter(Usuario.email == datos.email).first()

    if usuario:
        # asignar rol padre (si tu asignar_rol ya evita duplicados, perfecto)
        asignar_rol(db, usuario.id, "padre")

        # crear Padre solo si no existe
        padre = db.query(Padre).filter(Padre.usuario_id == usuario.id).first()
        if not padre:
            padre = Padre(
                usuario_id=usuario.id,
                parentesco="padre",
                notificaciones_activas=True
            )
            db.add(padre)
            db.commit()
            db.refresh(padre)

        return usuario

    # 2) Si no existe, crear y luego lo normal
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


# ✅ CAMBIO ÚNICO: esta ruta ya no se llama igual que la de token
@router.get("/verificar-email-disponible")
async def verificar_email_disponible(
    email: str,
    db: Session = Depends(get_db)
):
    """
    Verifica si un email ya está registrado en la base de datos.
    Retorna: { "disponible": true/false }
    """
    usuario_existe = db.query(Usuario).filter(Usuario.email == email).first()

    if usuario_existe:
        return {
            "disponible": False,
            "mensaje": "Este correo electrónico ya está registrado"
        }

    return {
        "disponible": True,
        "mensaje": "Correo disponible"
    }
