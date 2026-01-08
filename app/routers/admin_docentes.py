from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.config import get_db
from app.servicios.seguridad import requiere_admin
from app.esquemas.docente import (
    DocenteCreateAdmin,
    DocenteAdminResponse,
    DocenteUpdate,
)
from app.servicios.docente_admin import (
    crear_docente_admin,
    listar_docentes_admin,
    obtener_docente_admin,
    actualizar_docente_admin,
    eliminar_docente_admin,
)

router = APIRouter(prefix="/admin/docentes", tags=["admin-docentes"])


# ===========================================================
#   CREAR DOCENTE (ADMIN)
# ===========================================================
@router.post("", response_model=DocenteAdminResponse)
def crear_docente_route(
    data: DocenteCreateAdmin,
    db: Session = Depends(get_db),
    admin=Depends(requiere_admin),
):
    return crear_docente_admin(db, data)


# ===========================================================
#   LISTAR DOCENTES (ADMIN)
# ===========================================================
@router.get("", response_model=List[DocenteAdminResponse])
def listar_docentes_route(
    db: Session = Depends(get_db),
    admin=Depends(requiere_admin)
):
    return listar_docentes_admin(db)


# ===========================================================
#   OBTENER DOCENTE POR ID
# ===========================================================
@router.get("/{docente_id}", response_model=DocenteAdminResponse)
def obtener_docente_route(
    docente_id: int,
    db: Session = Depends(get_db),
    admin=Depends(requiere_admin)
):
    return obtener_docente_admin(db, docente_id)


# ===========================================================
#   ACTUALIZAR DOCENTE
# ===========================================================
@router.put("/{docente_id}", response_model=DocenteAdminResponse)
def actualizar_docente_route(
    docente_id: int,
    data: DocenteUpdate,
    db: Session = Depends(get_db),
    admin=Depends(requiere_admin)
):
    return actualizar_docente_admin(db, docente_id, data)


# ===========================================================
#   ELIMINAR DOCENTE
# ===========================================================
@router.delete("/{docente_id}")
def eliminar_docente_route(
    docente_id: int,
    db: Session = Depends(get_db),
    admin=Depends(requiere_admin)
):
    eliminar_docente_admin(db, docente_id)
    return {"mensaje": "Docente eliminado correctamente"}
