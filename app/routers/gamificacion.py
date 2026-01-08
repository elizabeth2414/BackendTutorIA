from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.config import get_db
from app.esquemas.gamificacion import (
    RecompensaCreate, RecompensaResponse,
    RecompensaEstudianteCreate, RecompensaEstudianteResponse,
    MisionDiariaCreate, MisionDiariaResponse,
    HistorialPuntosCreate, HistorialPuntosResponse
)
from app.servicios.gamificacion import (
    crear_recompensa, obtener_recompensas, obtener_recompensa,
    asignar_recompensa_estudiante, obtener_recompensas_estudiante,
    crear_mision_diaria, obtener_misiones_estudiante, actualizar_progreso_mision,
    agregar_puntos_estudiante, obtener_historial_puntos_estudiante
)
from app.servicios.seguridad import obtener_usuario_actual
from app.modelos import Usuario, Estudiante, NivelEstudiante

router = APIRouter(prefix="/gamificacion", tags=["gamificacion"])

# Endpoints para Recompensas
@router.post("/recompensas", response_model=RecompensaResponse)
def crear_nueva_recompensa(
    recompensa: RecompensaCreate,
    db: Session = Depends(get_db),
    usuario_actual: Usuario = Depends(obtener_usuario_actual)
):
    """Crear nueva recompensa"""
    return crear_recompensa(db, recompensa)

@router.get("/recompensas", response_model=List[RecompensaResponse])
def listar_recompensas(
    skip: int = 0,
    limit: int = 100,
    activo: bool = True,
    db: Session = Depends(get_db)
):
    """Listar recompensas disponibles"""
    return obtener_recompensas(db, skip=skip, limit=limit, activo=activo)

@router.get("/recompensas/{recompensa_id}", response_model=RecompensaResponse)
def obtener_recompensa_por_id(
    recompensa_id: int,
    db: Session = Depends(get_db)
):
    """Obtener recompensa por ID"""
    db_recompensa = obtener_recompensa(db, recompensa_id)
    if not db_recompensa:
        raise HTTPException(status_code=404, detail="Recompensa no encontrada")
    return db_recompensa

@router.post("/recompensas/estudiante", response_model=RecompensaEstudianteResponse)
def asignar_recompensa_a_estudiante(
    asignacion: RecompensaEstudianteCreate,
    db: Session = Depends(get_db),
    usuario_actual: Usuario = Depends(obtener_usuario_actual)
):
    """Asignar recompensa a estudiante"""
    return asignar_recompensa_estudiante(db, asignacion)

@router.get("/estudiante/{estudiante_id}/recompensas", response_model=List[RecompensaEstudianteResponse])
def listar_recompensas_estudiante(
    estudiante_id: int,
    db: Session = Depends(get_db),
    usuario_actual: Usuario = Depends(obtener_usuario_actual)
):
    """Listar recompensas de un estudiante"""
    return obtener_recompensas_estudiante(db, estudiante_id)

# Endpoints para Misiones Diarias
@router.post("/misiones", response_model=MisionDiariaResponse)
def crear_mision_diaria_estudiante(
    mision: MisionDiariaCreate,
    db: Session = Depends(get_db),
    usuario_actual: Usuario = Depends(obtener_usuario_actual)
):
    """Crear misión diaria para estudiante"""
    return crear_mision_diaria(db, mision)

@router.get("/estudiante/{estudiante_id}/misiones", response_model=List[MisionDiariaResponse])
def listar_misiones_estudiante(
    estudiante_id: int,
    fecha: str = None,
    db: Session = Depends(get_db),
    usuario_actual: Usuario = Depends(obtener_usuario_actual)
):
    """Listar misiones diarias de un estudiante"""
    return obtener_misiones_estudiante(db, estudiante_id, fecha)

@router.put("/misiones/{mision_id}/progreso")
def actualizar_progreso_mision_diaria(
    mision_id: int,
    progreso: int,
    db: Session = Depends(get_db),
    usuario_actual: Usuario = Depends(obtener_usuario_actual)
):
    """Actualizar progreso de misión diaria"""
    return actualizar_progreso_mision(db, mision_id, progreso)

# Endpoints para Puntos
@router.post("/puntos", response_model=HistorialPuntosResponse)
def agregar_puntos_estudiante(
    puntos: HistorialPuntosCreate,
    db: Session = Depends(get_db),
    usuario_actual: Usuario = Depends(obtener_usuario_actual)
):
    """Agregar puntos a estudiante"""
    return agregar_puntos_estudiante(db, puntos)

@router.get("/estudiante/{estudiante_id}/puntos", response_model=List[HistorialPuntosResponse])
def listar_historial_puntos_estudiante(
    estudiante_id: int,
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
    usuario_actual: Usuario = Depends(obtener_usuario_actual)
):
    """Listar historial de puntos de un estudiante"""
    return obtener_historial_puntos_estudiante(db, estudiante_id, skip, limit)


@router.get("/estudiante/{estudiante_id}/progreso")
def obtener_progreso_estudiante(
    estudiante_id: int,
    db: Session = Depends(get_db),
    usuario_actual: Usuario = Depends(obtener_usuario_actual)
):
    """
    Obtener progreso gamificado del estudiante
    (nivel, puntos, racha, etc.)
    """

    estudiante = db.query(Estudiante).filter(
        Estudiante.id == estudiante_id
    ).first()

    if not estudiante:
        raise HTTPException(status_code=404, detail="Estudiante no encontrado")

    nivel = db.query(NivelEstudiante).filter(
        NivelEstudiante.estudiante_id == estudiante_id
    ).first()

    if not nivel:
        raise HTTPException(status_code=404, detail="Progreso del estudiante no encontrado")

    return {
        "id": estudiante.id,
        "nombre": estudiante.nombre,
        "nivel_actual": nivel.nivel_actual,
        "xp_actual": nivel.puntos_nivel_actual,
        "xp_para_siguiente_nivel": nivel.puntos_para_siguiente_nivel,
        "racha_actual": nivel.racha_actual,
    }
