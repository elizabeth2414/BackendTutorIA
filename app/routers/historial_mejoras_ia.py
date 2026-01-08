from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List

from app.config import get_db
from app.servicios.seguridad import obtener_usuario_actual
from app.modelos import Usuario, Estudiante
from app.modelos.historial_mejoras_ia import HistorialMejorasIA
from app.esquemas.historial_mejoras_ia import HistorialMejorasIAResponse
from app.routers import (
    historial_pronunciacion,
    historial_practica_pronunciacion,
    historial_mejoras_ia,
)

router = APIRouter(
    prefix="/historial/mejoras",
    tags=["Historial Mejoras IA"]
)


@router.get(
    "/mis",
    response_model=List[HistorialMejorasIAResponse]
)
def obtener_mis_mejoras_ia(
    db: Session = Depends(get_db),
    usuario_actual: Usuario = Depends(obtener_usuario_actual)
):
    estudiante = (
        db.query(Estudiante)
        .filter(Estudiante.usuario_id == usuario_actual.id)
        .first()
    )

    if not estudiante:
        return []

    return (
        db.query(HistorialMejorasIA)
        .filter(HistorialMejorasIA.estudiante_id == estudiante.id)
        .order_by(HistorialMejorasIA.fecha.desc())
        .all()
    )
