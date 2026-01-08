# app/scripts/crear_admin_inicial.py

from app.config import SessionLocal
from app.modelos import Usuario
from app.modelos.usuario_rol import UsuarioRol  # ⬅️ ajusta el import si tu modelo está en otro archivo
from app.servicios.seguridad import obtener_password_hash


def crear_admin_inicial():
    db = SessionLocal()

    # 👇 CONFIGURA AQUÍ LAS CREDENCIALES DEL ADMIN
    email_admin = "admin@tutoria.com"
    password_plano = "AdminIA2025@"
    nombre_admin = "Admin"
    apellido_admin = "Principal"

    print("🔍 Buscando si ya existe el admin...")

    existente = (
        db.query(Usuario)
        .filter(Usuario.email == email_admin)
        .first()
    )

    if existente:
        print(f"✅ Ya existe un usuario con email {email_admin} (id={existente.id})")

        # Verificamos si ya tiene rol admin
        rol_admin = (
            db.query(UsuarioRol)
            .filter(
                UsuarioRol.usuario_id == existente.id,
                UsuarioRol.rol == "admin",
            )
            .first()
        )
        if rol_admin:
            print("✅ Ese usuario ya tiene rol 'admin'. No hay nada que hacer.")
            db.close()
            return
        else:
            print("⚠️ Usuario existe pero sin rol 'admin'. Asignando rol...")

            nuevo_rol = UsuarioRol(
                usuario_id=existente.id,
                rol="admin",
            )
            db.add(nuevo_rol)
            db.commit()
            print("✅ Rol 'admin' asignado correctamente.")
            db.close()
            return

    # Si NO existe, lo creamos
    print("🆕 Creando usuario admin...")

    password_hash = obtener_password_hash(password_plano)

    admin = Usuario(
        email=email_admin,
        password_hash=password_hash,
        nombre=nombre_admin,
        apellido=apellido_admin,
    )
    db.add(admin)
    db.commit()
    db.refresh(admin)

    print(f"✅ Usuario admin creado con id={admin.id}")

    # Asignar rol admin
    rol = UsuarioRol(
        usuario_id=admin.id,
        rol="admin",
    )
    db.add(rol)
    db.commit()

    print("✅ Rol 'admin' asignado")
    print("🎉 Admin listo para usar:")
    print(f"   Email: {email_admin}")
    print(f"   Password: {password_plano}")

    db.close()


if __name__ == "__main__":
    crear_admin_inicial()
