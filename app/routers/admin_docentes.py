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
from app.servicios.auth import configurar_cuenta_docente

from pydantic import BaseModel

router = APIRouter(prefix="/admin/docentes", tags=["admin-docentes"])



@router.post("", response_model=DocenteAdminResponse)
def crear_docente_route(
    data: DocenteCreateAdmin,
    db: Session = Depends(get_db),
    admin=Depends(requiere_admin),
):
    return crear_docente_admin(db, data)



@router.get("", response_model=List[DocenteAdminResponse])
def listar_docentes_route(
    db: Session = Depends(get_db),
    admin=Depends(requiere_admin)
):
    return listar_docentes_admin(db)



@router.get("/{docente_id}", response_model=DocenteAdminResponse)
def obtener_docente_route(
    docente_id: int,
    db: Session = Depends(get_db),
    admin=Depends(requiere_admin)
):
    return obtener_docente_admin(db, docente_id)



@router.put("/{docente_id}", response_model=DocenteAdminResponse)
def actualizar_docente_route(
    docente_id: int,
    data: DocenteUpdate,
    db: Session = Depends(get_db),
    admin=Depends(requiere_admin)
):
    return actualizar_docente_admin(db, docente_id, data)



@router.delete("/{docente_id}")
def eliminar_docente_route(
    docente_id: int,
    db: Session = Depends(get_db),
    admin=Depends(requiere_admin)
):
    eliminar_docente_admin(db, docente_id)
    return {"mensaje": "Docente eliminado correctamente"}

@router.patch("/{docente_id}/toggle", response_model=DocenteAdminResponse)
def toggle_docente_route(
    docente_id: int,
    db: Session = Depends(get_db),
    admin=Depends(requiere_admin)
):
    """
    Activa o desactiva un docente (NO lo elimina).
    """
    from app.servicios.docente_admin import toggle_docente_admin
    return toggle_docente_admin(db, docente_id)

class ConfigurarCuentaRequest(BaseModel):
    token: str
    nuevo_password: str

@router.post("/configurar-cuenta")
def configurar_cuenta_endpoint(
    request: ConfigurarCuentaRequest,
    db: Session = Depends(get_db)
):
    return configurar_cuenta_docente(db, request.token, request.nuevo_password)
