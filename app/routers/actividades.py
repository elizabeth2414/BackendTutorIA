from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.config import get_db
from app.esquemas.actividad import (
    ActividadCreate, ActividadResponse, ActividadUpdate,
    PreguntaCreate, PreguntaResponse,
    ProgresoActividadCreate, ProgresoActividadResponse,
    RespuestaPreguntaCreate, RespuestaPreguntaResponse
)
from app.servicios.actividad import (
    crear_actividad, obtener_actividades, obtener_actividad,
    actualizar_actividad, eliminar_actividad,
    crear_pregunta, obtener_preguntas_actividad,
    crear_progreso_actividad, obtener_progreso_estudiante,
    crear_respuesta_pregunta, obtener_respuestas_progreso
)
from app.servicios.seguridad import obtener_usuario_actual
from app.modelos import Usuario

router = APIRouter(prefix="/actividades", tags=["actividades"])

@router.post("/", response_model=ActividadResponse)
def crear_actividad_educativa(
    actividad: ActividadCreate,
    db: Session = Depends(get_db),
    usuario_actual: Usuario = Depends(obtener_usuario_actual)
):
    """Crear nueva actividad educativa"""
    return crear_actividad(db, actividad)

@router.get("/", response_model=List[ActividadResponse])
def listar_actividades(
    skip: int = 0,
    limit: int = 100,
    contenido_id: int = None,
    activo: bool = True,
    db: Session = Depends(get_db)
):
    """Listar actividades educativas"""
    return obtener_actividades(db, skip=skip, limit=limit, 
                              contenido_id=contenido_id, activo=activo)

@router.get("/{actividad_id}", response_model=ActividadResponse)
def obtener_actividad_por_id(
    actividad_id: int,
    db: Session = Depends(get_db)
):
    """Obtener actividad por ID"""
    db_actividad = obtener_actividad(db, actividad_id)
    if not db_actividad:
        raise HTTPException(status_code=404, detail="Actividad no encontrada")
    return db_actividad

@router.put("/{actividad_id}", response_model=ActividadResponse)
def actualizar_actividad(
    actividad_id: int,
    actividad: ActividadUpdate,
    db: Session = Depends(get_db),
    usuario_actual: Usuario = Depends(obtener_usuario_actual)
):
    """Actualizar actividad"""
    return actualizar_actividad(db, actividad_id, actividad)

@router.delete("/{actividad_id}")
def eliminar_actividad(
    actividad_id: int,
    db: Session = Depends(get_db),
    usuario_actual: Usuario = Depends(obtener_usuario_actual)
):
    """Eliminar actividad (soft delete)"""
    eliminar_actividad(db, actividad_id)
    return {"mensaje": "Actividad eliminada correctamente"}

@router.post("/{actividad_id}/preguntas", response_model=PreguntaResponse)
def agregar_pregunta(
    actividad_id: int,
    pregunta: PreguntaCreate,
    db: Session = Depends(get_db),
    usuario_actual: Usuario = Depends(obtener_usuario_actual)
):
    """Agregar pregunta a actividad"""
    return crear_pregunta(db, actividad_id, pregunta)

@router.get("/{actividad_id}/preguntas", response_model=List[PreguntaResponse])
def listar_preguntas_actividad(
    actividad_id: int,
    db: Session = Depends(get_db)
):
    """Listar preguntas de una actividad"""
    return obtener_preguntas_actividad(db, actividad_id)

@router.post("/progreso", response_model=ProgresoActividadResponse)
def registrar_progreso(
    progreso: ProgresoActividadCreate,
    db: Session = Depends(get_db),
    usuario_actual: Usuario = Depends(obtener_usuario_actual)
):
    """Registrar progreso en actividad"""
    return crear_progreso_actividad(db, progreso)

@router.get("/estudiante/{estudiante_id}/progreso", response_model=List[ProgresoActividadResponse])
def listar_progreso_estudiante(
    estudiante_id: int,
    db: Session = Depends(get_db),
    usuario_actual: Usuario = Depends(obtener_usuario_actual)
):
    """Listar progreso de actividades de un estudiante"""
    return obtener_progreso_estudiante(db, estudiante_id)

@router.post("/progreso/{progreso_id}/respuestas", response_model=RespuestaPreguntaResponse)
def agregar_respuesta_pregunta(
    progreso_id: int,
    respuesta: RespuestaPreguntaCreate,
    db: Session = Depends(get_db),
    usuario_actual: Usuario = Depends(obtener_usuario_actual)
):
    """Agregar respuesta a pregunta"""
    return crear_respuesta_pregunta(db, progreso_id, respuesta)

@router.get("/progreso/{progreso_id}/respuestas", response_model=List[RespuestaPreguntaResponse])
def listar_respuestas_progreso(
    progreso_id: int,
    db: Session = Depends(get_db),
    usuario_actual: Usuario = Depends(obtener_usuario_actual)
):
    """Listar respuestas de un progreso"""
    return obtener_respuestas_progreso(db, progreso_id)