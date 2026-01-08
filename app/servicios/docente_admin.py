from typing import List, Optional
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from datetime import datetime

from app.modelos import Usuario, UsuarioRol, Docente
from app.esquemas.docente import DocenteCreateAdmin, DocenteUpdate
from app.servicios.seguridad import obtener_password_hash

def crear_docente_admin(db: Session, data: DocenteCreateAdmin) -> Docente:

    # 1. Validar email repetido
    if db.query(Usuario).filter(Usuario.email == data.email).first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Ya existe un usuario con ese email",
        )

    try:
        # 2. Convertir fecha (si viene vacía la ponemos como None)
        fecha_contratacion = None
        if data.fecha_contratacion not in ["", None]:
            fecha_contratacion = datetime.strptime(
                str(data.fecha_contratacion), "%Y-%m-%d"
            ).date()

        # 3. Crear usuario
        usuario = Usuario(
            email=data.email,
            password_hash=obtener_password_hash(data.password),
            nombre=data.nombre,
            apellido=data.apellido,
            activo=True,
        )
        db.add(usuario)
        db.flush()  # obtener usuario.id

        # 4. Asignar rol docente
        rol = UsuarioRol(
            usuario_id=usuario.id,
            rol="docente",
            activo=True,
        )
        db.add(rol)

        # 5. Crear docente
        docente = Docente(
            usuario_id=usuario.id,
            especialidad=data.especialidad,
            grado_academico=data.grado_academico,
            institucion=data.institucion,
            fecha_contratacion=fecha_contratacion,
            activo=True,
        )
        db.add(docente)

        # 6. Guardar cambios
        db.commit()
        db.refresh(docente)

        return docente

    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Error interno al crear docente: {str(e)}",
        )


# ===========================================================
# LISTAR
# ===========================================================
def listar_docentes_admin(db: Session, activo: Optional[bool] = None) -> List[Docente]:

    query = db.query(Docente).join(Usuario, Docente.usuario_id == Usuario.id)

    if activo is not None:
        query = query.filter(Docente.activo == activo)

    return query.all()


# ===========================================================
# OBTENER
# ===========================================================
def obtener_docente_admin(db: Session, docente_id: int) -> Docente:
    docente = db.query(Docente).filter(Docente.id == docente_id).first()
    if not docente:
        raise HTTPException(404, "Docente no encontrado")
    return docente


def actualizar_docente_admin(db: Session, docente_id: int, data: DocenteUpdate) -> Docente:

    docente = obtener_docente_admin(db, docente_id)

    update_data = data.dict(exclude_unset=True)

    # Manejar fecha correctamente
    if "fecha_contratacion" in update_data:
        if update_data["fecha_contratacion"] in ["", None]:
            update_data["fecha_contratacion"] = None

    for field, value in update_data.items():
        setattr(docente, field, value)

    db.commit()
    db.refresh(docente)

    return docente

# ===========================================================
# DESACTIVAR
# ===========================================================
def eliminar_docente_admin(db: Session, docente_id: int) -> Docente:

    docente = obtener_docente_admin(db, docente_id)

    docente.activo = False

    if docente.usuario:
        docente.usuario.activo = False

    db.commit()
    db.refresh(docente)

    return docente
