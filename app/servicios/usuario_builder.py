from app.esquemas.auth import UsuarioResponse
from app.modelos import UsuarioRol


def build_usuario_response(db, usuario):
    roles_rows = (
        db.query(UsuarioRol.rol)
        .filter(
            UsuarioRol.usuario_id == usuario.id,
            UsuarioRol.activo == True,
        )
        .all()
    )

    roles_nombres = [r[0] for r in roles_rows]

    return UsuarioResponse(
        id=usuario.id,
        email=usuario.email,
        nombre=usuario.nombre,
        apellido=usuario.apellido,
        activo=usuario.activo,
        email_verificado=usuario.email_verificado,
        bloqueado=usuario.bloqueado,
        fecha_creacion=usuario.fecha_creacion,
        ultimo_login=usuario.ultimo_login,
        roles_nombres=roles_nombres,
    )
