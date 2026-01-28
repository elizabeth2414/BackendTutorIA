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
    ResetPasswordConfirm,
    ConfigurarCuentaRequest
)

from app.servicios.auth import (
    autenticar_usuario,
    crear_usuario,
    cambiar_password,
    resetear_password,
    confirmar_reset_password,
    verificar_email,          
    reenviar_verificacion  ,
    configurar_cuenta_docente   
)

from app.servicios.seguridad import (
    obtener_usuario_actual,
    crear_token_acceso,
    asignar_rol
)

from app.servicios.usuario_builder import build_usuario_response


router = APIRouter(prefix="/auth", tags=["autenticacion"])

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")



class ReenviarVerificacionRequest(BaseModel):
    email: EmailStr



@router.post("/registro", response_model=UsuarioResponse)
def registro(usuario: UsuarioCreate, db: Session = Depends(get_db)):
    return crear_usuario(db, usuario)



@router.post("/login", response_model=Token)
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    # autenticar_usuario ahora puede lanzar HTTPException 403
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



@router.get("/verificar-email")
def verificar_email_endpoint(
    token: str = Query(..., min_length=10),
    db: Session = Depends(get_db)
):
    return verificar_email(db, token)



@router.post("/reenviar-verificacion")
def reenviar_verificacion_endpoint(
    request: ReenviarVerificacionRequest,
    db: Session = Depends(get_db)
):
    return reenviar_verificacion(db, request.email)



@router.post("/cambio-password")
def cambio_password_endpoint(
    cambio: CambioPassword,
    db: Session = Depends(get_db),
    usuario_actual: Usuario = Depends(obtener_usuario_actual)
):
    return cambiar_password(db, usuario_actual.id, cambio)



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



@router.post("/registro-padre", response_model=UsuarioResponse)
def registro_padre(datos: UsuarioCreate, db: Session = Depends(get_db)):
 
    usuario = db.query(Usuario).filter(Usuario.email == datos.email).first()

    if usuario:
      
        asignar_rol(db, usuario.id, "padre")

    
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

        return build_usuario_response(db, usuario)

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

    return build_usuario_response(db, nuevo_usuario)



@router.get("/verificar-email-disponible")
def verificar_email_disponible(
    email: EmailStr,
    db: Session = Depends(get_db)
):
    email_norm = email.strip().lower()

    usuario_existe = db.query(Usuario).filter(
        Usuario.email.ilike(email_norm)
    ).first()

    return {
        "disponible": not bool(usuario_existe),
        "mensaje": "Correo disponible" if not usuario_existe else "Este correo electrónico ya está registrado"
    }

@router.post("/configurar-cuenta")
def configurar_cuenta_endpoint(
    request: ConfigurarCuentaRequest,
    db: Session = Depends(get_db)
):
    return configurar_cuenta_docente(db, request.token, request.nuevo_password)
