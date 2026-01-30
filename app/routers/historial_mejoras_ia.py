from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.config import get_db
from app.servicios.seguridad import obtener_usuario_actual, obtener_docente_actual
from app.modelos import Usuario, Estudiante, Padre, Docente
from app.modelos.historial_mejoras_ia import HistorialMejorasIA
from app.esquemas.historial_mejoras_ia import HistorialMejorasIAResponse
 

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


@router.get(
    "/hijo/{estudiante_id}",
    response_model=List[HistorialMejorasIAResponse]
)
def obtener_mejoras_ia_hijo(
    estudiante_id: int,
    db: Session = Depends(get_db),
    usuario_actual: Usuario = Depends(obtener_usuario_actual),
):
    """Mejoras IA (tutor) para vista padre."""
    padre = db.query(Padre).filter(Padre.usuario_id == usuario_actual.id).first()
    if not padre:
        raise HTTPException(403, "Acceso solo para padres")

    estudiante = (
        db.query(Estudiante)
        .filter(Estudiante.id == estudiante_id, Estudiante.padre_id == padre.id)
        .first()
    )
    if not estudiante:
        raise HTTPException(403, "No autorizado")

    return (
        db.query(HistorialMejorasIA)
        .filter(HistorialMejorasIA.estudiante_id == estudiante.id)
        .order_by(HistorialMejorasIA.fecha.desc())
        .all()
    )


@router.get(
    "/docente/{estudiante_id}",
    response_model=List[HistorialMejorasIAResponse]
)
@router.get(
    "/estudiante/{estudiante_id}",
    response_model=List[HistorialMejorasIAResponse]
)
def obtener_mejoras_ia_estudiante_docente(
    estudiante_id: int,
    db: Session = Depends(get_db),
    docente: Docente = Depends(obtener_docente_actual),
):
    """Mejoras IA (tutor) para vista docente."""
    estudiante = (
        db.query(Estudiante)
        .filter(Estudiante.id == estudiante_id, Estudiante.docente_id == docente.id)
        .first()
    )
    if not estudiante:
        raise HTTPException(403, "No autorizado")

    return (
        db.query(HistorialMejorasIA)
        .filter(HistorialMejorasIA.estudiante_id == estudiante.id)
        .order_by(HistorialMejorasIA.fecha.desc())
        .all()
    )
