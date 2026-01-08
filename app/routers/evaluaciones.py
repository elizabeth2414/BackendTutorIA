from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.config import get_db
from app.esquemas.evaluacion import (
    EvaluacionLecturaCreate, EvaluacionLecturaResponse,
    AnalisisIACreate, AnalisisIAResponse,
    IntentoLecturaCreate, IntentoLecturaResponse,
    DetalleEvaluacionCreate, DetalleEvaluacionResponse,
    ErrorPronunciacionCreate, ErrorPronunciacionResponse
)
from app.servicios.evaluacion import (
    crear_evaluacion, obtener_evaluaciones, obtener_evaluacion,
    crear_analisis_ia, obtener_analisis_evaluacion,
    crear_intento_lectura, obtener_intentos_evaluacion,
    crear_detalle_evaluacion, obtener_detalles_evaluacion,
    crear_error_pronunciacion
)
from app.servicios.seguridad import obtener_usuario_actual
from app.modelos import Usuario

router = APIRouter(prefix="/evaluaciones", tags=["evaluaciones"])

@router.post("/", response_model=EvaluacionLecturaResponse)
def crear_evaluacion_lectura(
    evaluacion: EvaluacionLecturaCreate,
    db: Session = Depends(get_db),
    usuario_actual: Usuario = Depends(obtener_usuario_actual)
):
    """Crear nueva evaluación de lectura"""
    return crear_evaluacion(db, evaluacion)

@router.get("/", response_model=List[EvaluacionLecturaResponse])
def listar_evaluaciones(
    skip: int = 0,
    limit: int = 100,
    estudiante_id: int = None,
    contenido_id: int = None,
    db: Session = Depends(get_db),
    usuario_actual: Usuario = Depends(obtener_usuario_actual)
):
    """Listar evaluaciones"""
    return obtener_evaluaciones(db, skip=skip, limit=limit, 
                               estudiante_id=estudiante_id, contenido_id=contenido_id)

@router.get("/{evaluacion_id}", response_model=EvaluacionLecturaResponse)
def obtener_evaluacion_por_id(
    evaluacion_id: int,
    db: Session = Depends(get_db),
    usuario_actual: Usuario = Depends(obtener_usuario_actual)
):
    """Obtener evaluación por ID"""
    db_evaluacion = obtener_evaluacion(db, evaluacion_id)
    if not db_evaluacion:
        raise HTTPException(status_code=404, detail="Evaluación no encontrada")
    return db_evaluacion

@router.post("/{evaluacion_id}/analisis-ia", response_model=AnalisisIAResponse)
def agregar_analisis_ia(
    evaluacion_id: int,
    analisis: AnalisisIACreate,
    db: Session = Depends(get_db),
    usuario_actual: Usuario = Depends(obtener_usuario_actual)
):
    """Agregar análisis de IA a evaluación"""
    return crear_analisis_ia(db, evaluacion_id, analisis)

@router.get("/{evaluacion_id}/analisis-ia", response_model=AnalisisIAResponse)
def obtener_analisis_ia(
    evaluacion_id: int,
    db: Session = Depends(get_db),
    usuario_actual: Usuario = Depends(obtener_usuario_actual)
):
    """Obtener análisis de IA de evaluación"""
    return obtener_analisis_evaluacion(db, evaluacion_id)

@router.post("/{evaluacion_id}/intentos", response_model=IntentoLecturaResponse)
def agregar_intento_lectura(
    evaluacion_id: int,
    intento: IntentoLecturaCreate,
    db: Session = Depends(get_db),
    usuario_actual: Usuario = Depends(obtener_usuario_actual)
):
    """Agregar intento de lectura"""
    return crear_intento_lectura(db, evaluacion_id, intento)

@router.get("/{evaluacion_id}/intentos", response_model=List[IntentoLecturaResponse])
def listar_intentos_evaluacion(
    evaluacion_id: int,
    db: Session = Depends(get_db),
    usuario_actual: Usuario = Depends(obtener_usuario_actual)
):
    """Listar intentos de una evaluación"""
    return obtener_intentos_evaluacion(db, evaluacion_id)

@router.post("/{evaluacion_id}/detalles", response_model=DetalleEvaluacionResponse)
def agregar_detalle_evaluacion(
    evaluacion_id: int,
    detalle: DetalleEvaluacionCreate,
    db: Session = Depends(get_db),
    usuario_actual: Usuario = Depends(obtener_usuario_actual)
):
    """Agregar detalle de evaluación"""
    return crear_detalle_evaluacion(db, evaluacion_id, detalle)

@router.get("/{evaluacion_id}/detalles", response_model=List[DetalleEvaluacionResponse])
def listar_detalles_evaluacion(
    evaluacion_id: int,
    db: Session = Depends(get_db),
    usuario_actual: Usuario = Depends(obtener_usuario_actual)
):
    """Listar detalles de una evaluación"""
    return obtener_detalles_evaluacion(db, evaluacion_id)

@router.post("/detalles/{detalle_id}/errores", response_model=ErrorPronunciacionResponse)
def agregar_error_pronunciacion(
    detalle_id: int,
    error: ErrorPronunciacionCreate,
    db: Session = Depends(get_db),
    usuario_actual: Usuario = Depends(obtener_usuario_actual)
):
    """Agregar error de pronunciación"""
    return crear_error_pronunciacion(db, detalle_id, error)