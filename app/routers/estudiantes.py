# app/routers/estudiantes.py

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.config import get_db
from app.esquemas.estudiante import (
    EstudianteCreate, EstudianteResponse, EstudianteUpdate,
    NivelEstudianteResponse
)
from app.servicios.estudiante import (
    crear_estudiante, obtener_estudiantes, obtener_estudiante,
    actualizar_estudiante as actualizar_estudiante_service,
    eliminar_estudiante as eliminar_estudiante_service,
    obtener_nivel_estudiante
)
from app.servicios.seguridad import obtener_usuario_actual
from app.modelos import Usuario

# 🚀 PREFIX ORIGINAL — SE MANTIENE
router = APIRouter(prefix="/estudiantes", tags=["estudiantes"])


# ============================================================
#           CREAR ESTUDIANTE (modo general)
# ============================================================
@router.post("/", response_model=EstudianteResponse)
def crear_nuevo_estudiante(
    estudiante: EstudianteCreate,
    db: Session = Depends(get_db),
    usuario_actual: Usuario = Depends(obtener_usuario_actual)
):
    return crear_estudiante(db, estudiante)


# ============================================================
#           LISTAR ESTUDIANTES
# ============================================================
@router.get("/", response_model=List[EstudianteResponse])
def listar_estudiantes(
    skip: int = 0,
    limit: int = 100,
    docente_id: int = None,
    activo: bool = True,
    db: Session = Depends(get_db),
    usuario_actual: Usuario = Depends(obtener_usuario_actual)
):
    return obtener_estudiantes(
        db,
        skip=skip,
        limit=limit,
        docente_id=docente_id,
        activo=activo
    )


# ============================================================
#           OBTENER ESTUDIANTE POR ID  (CORREGIDO)
# ============================================================
@router.get("/{estudiante_id:int}", response_model=EstudianteResponse)
def obtener_estudiante_por_id(
    estudiante_id: int,
    db: Session = Depends(get_db),
    usuario_actual: Usuario = Depends(obtener_usuario_actual)
):
    db_estudiante = obtener_estudiante(db, estudiante_id)
    if not db_estudiante:
        raise HTTPException(status_code=404, detail="Estudiante no encontrado")
    return db_estudiante


# ============================================================
#           ACTUALIZAR ESTUDIANTE (CORREGIDO)
# ============================================================
@router.put("/{estudiante_id:int}", response_model=EstudianteResponse)
def actualizar_estudiante(
    estudiante_id: int,
    estudiante: EstudianteUpdate,
    db: Session = Depends(get_db),
    usuario_actual: Usuario = Depends(obtener_usuario_actual)
):
    return actualizar_estudiante_service(db, estudiante_id, estudiante)


# ============================================================
#           ELIMINAR ESTUDIANTE (CORREGIDO)
# ============================================================
@router.delete("/{estudiante_id:int}")
def eliminar_estudiante(
    estudiante_id: int,
    db: Session = Depends(get_db),
    usuario_actual: Usuario = Depends(obtener_usuario_actual)
):
    eliminar_estudiante_service(db, estudiante_id)
    return {"mensaje": "Estudiante eliminado correctamente"}


# ============================================================
#           NIVEL DEL ESTUDIANTE (CORREGIDO)
# ============================================================
@router.get("/{estudiante_id:int}/nivel", response_model=NivelEstudianteResponse)
def obtener_nivel(
    estudiante_id: int,
    db: Session = Depends(get_db),
    usuario_actual: Usuario = Depends(obtener_usuario_actual)
):
    return obtener_nivel_estudiante(db, estudiante_id)
