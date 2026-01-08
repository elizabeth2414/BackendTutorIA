from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List

from app.config import get_db
from app.servicios.seguridad import requiere_admin
from app.modelos import Estudiante, Usuario

router = APIRouter(prefix="/admin", tags=["Admin Estudiantes"])

@router.get("/estudiantes")
def listar_estudiantes_admin(
    db: Session = Depends(get_db),
    admin: Usuario = Depends(requiere_admin)  # ✅ Validación de rol usando dependency
):
    """
    Lista todos los estudiantes del sistema (vista administrativa).

    Requiere rol: admin

    Returns:
        List[Estudiante]: Lista de todos los estudiantes
    """
    estudiantes = db.query(Estudiante).all()
    return estudiantes
