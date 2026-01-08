from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from datetime import date

from app.config  import get_db
from app.esquemas.estadisticas import (
    EstadisticasEstudiante, ProgresoCurso, ReporteEvaluacion,
    TendenciaProgreso, DashboardDocente
)
from app.servicios.estadisticas import (
    obtener_estadisticas_estudiante, obtener_progreso_cursos,
    obtener_reportes_evaluacion, obtener_tendencias_progreso,
    obtener_dashboard_docente
)
from app.servicios.seguridad import obtener_usuario_actual
from app.modelos import Usuario

router = APIRouter(prefix="/estadisticas", tags=["estadisticas"])

@router.get("/estudiante/{estudiante_id}", response_model=EstadisticasEstudiante)
def obtener_estadisticas_estudiante_por_id(
    estudiante_id: int,
    db: Session = Depends(get_db),
    usuario_actual: Usuario = Depends(obtener_usuario_actual)
):
    """Obtener estadísticas completas de un estudiante"""
    return obtener_estadisticas_estudiante(db, estudiante_id)

@router.get("/cursos/{docente_id}", response_model=List[ProgresoCurso])
def obtener_progreso_cursos_docente(
    docente_id: int,
    db: Session = Depends(get_db),
    usuario_actual: Usuario = Depends(obtener_usuario_actual)
):
    """Obtener progreso de todos los cursos de un docente"""
    return obtener_progreso_cursos(db, docente_id)

@router.get("/evaluaciones/{estudiante_id}", response_model=List[ReporteEvaluacion])
def obtener_reportes_evaluacion_estudiante(
    estudiante_id: int,
    limite: int = 10,
    db: Session = Depends(get_db),
    usuario_actual: Usuario = Depends(obtener_usuario_actual)
):
    """Obtener reportes de evaluaciones de un estudiante"""
    return obtener_reportes_evaluacion(db, estudiante_id, limite)

@router.get("/tendencias/{estudiante_id}", response_model=List[TendenciaProgreso])
def obtener_tendencias_progreso_estudiante(
    estudiante_id: int,
    dias: int = 30,
    db: Session = Depends(get_db),
    usuario_actual: Usuario = Depends(obtener_usuario_actual)
):
    """Obtener tendencias de progreso de un estudiante"""
    return obtener_tendencias_progreso(db, estudiante_id, dias)

@router.get("/dashboard/docente/{docente_id}", response_model=DashboardDocente)
def obtener_dashboard_docente(
    docente_id: int,
    db: Session = Depends(get_db),
    usuario_actual: Usuario = Depends(obtener_usuario_actual)
):
    """Obtener dashboard completo para docente"""
    return obtener_dashboard_docente(db, docente_id)