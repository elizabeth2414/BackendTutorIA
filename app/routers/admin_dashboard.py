from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.config import get_db
from app.servicios.seguridad import requiere_admin
from app.modelos import Usuario
from app.esquemas.dashboard import DashboardStats
from app.servicios.dashboard import obtener_estadisticas_dashboard

router = APIRouter(prefix="/admin", tags=["Admin Dashboard"])

@router.get("/dashboard", response_model=DashboardStats)
def obtener_dashboard(
    db: Session = Depends(get_db),
    admin: Usuario = Depends(requiere_admin)  # ✅ Validación de rol usando dependency
):
    """
    Obtiene estadísticas del dashboard administrativo.

    Requiere rol: admin

    Returns:
        DashboardStats: Estadísticas generales del sistema
    """
    return obtener_estadisticas_dashboard(db)
