from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.config import get_db
from app.esquemas.ejercicio import (
    EjercicioPracticaCreate, EjercicioPracticaResponse, EjercicioPracticaUpdate,
    ResultadoEjercicioCreate, ResultadoEjercicioResponse,
    FragmentoPracticaCreate, FragmentoPracticaResponse
)
from app.servicios.ejercicio import (
    crear_ejercicio, obtener_ejercicios, obtener_ejercicio,
    actualizar_ejercicio, eliminar_ejercicio,
    crear_resultado_ejercicio, obtener_resultados_ejercicio,
    crear_fragmento_practica, obtener_fragmentos_ejercicio
)
from app.servicios.seguridad import obtener_usuario_actual
from app.modelos import Usuario

router = APIRouter(prefix="/ejercicios", tags=["ejercicios"])

@router.post("/", response_model=EjercicioPracticaResponse)
def crear_ejercicio_practica(
    ejercicio: EjercicioPracticaCreate,
    db: Session = Depends(get_db),
    usuario_actual: Usuario = Depends(obtener_usuario_actual)
):
    """Crear nuevo ejercicio de práctica"""
    return crear_ejercicio(db, ejercicio)

@router.get("/", response_model=List[EjercicioPracticaResponse])
def listar_ejercicios(
    skip: int = 0,
    limit: int = 100,
    estudiante_id: int = None,
    evaluacion_id: int = None,
    completado: bool = None,
    db: Session = Depends(get_db),
    usuario_actual: Usuario = Depends(obtener_usuario_actual)
):
    """Listar ejercicios de práctica"""
    return obtener_ejercicios(db, skip=skip, limit=limit, 
                             estudiante_id=estudiante_id, evaluacion_id=evaluacion_id,
                             completado=completado)

@router.get("/{ejercicio_id}", response_model=EjercicioPracticaResponse)
def obtener_ejercicio_por_id(
    ejercicio_id: int,
    db: Session = Depends(get_db),
    usuario_actual: Usuario = Depends(obtener_usuario_actual)
):
    """Obtener ejercicio por ID"""
    db_ejercicio = obtener_ejercicio(db, ejercicio_id)
    if not db_ejercicio:
        raise HTTPException(status_code=404, detail="Ejercicio no encontrado")
    return db_ejercicio

@router.put("/{ejercicio_id}", response_model=EjercicioPracticaResponse)
def actualizar_ejercicio(
    ejercicio_id: int,
    ejercicio: EjercicioPracticaUpdate,
    db: Session = Depends(get_db),
    usuario_actual: Usuario = Depends(obtener_usuario_actual)
):
    """Actualizar ejercicio"""
    return actualizar_ejercicio(db, ejercicio_id, ejercicio)

@router.delete("/{ejercicio_id}")
def eliminar_ejercicio(
    ejercicio_id: int,
    db: Session = Depends(get_db),
    usuario_actual: Usuario = Depends(obtener_usuario_actual)
):
    """Eliminar ejercicio (soft delete)"""
    eliminar_ejercicio(db, ejercicio_id)
    return {"mensaje": "Ejercicio eliminado correctamente"}

@router.post("/{ejercicio_id}/resultados", response_model=ResultadoEjercicioResponse)
def agregar_resultado_ejercicio(
    ejercicio_id: int,
    resultado: ResultadoEjercicioCreate,
    db: Session = Depends(get_db),
    usuario_actual: Usuario = Depends(obtener_usuario_actual)
):
    """Agregar resultado de ejercicio"""
    return crear_resultado_ejercicio(db, ejercicio_id, resultado)

@router.get("/{ejercicio_id}/resultados", response_model=List[ResultadoEjercicioResponse])
def listar_resultados_ejercicio(
    ejercicio_id: int,
    db: Session = Depends(get_db),
    usuario_actual: Usuario = Depends(obtener_usuario_actual)
):
    """Listar resultados de un ejercicio"""
    return obtener_resultados_ejercicio(db, ejercicio_id)

@router.post("/{ejercicio_id}/fragmentos", response_model=FragmentoPracticaResponse)
def agregar_fragmento_practica(
    ejercicio_id: int,
    fragmento: FragmentoPracticaCreate,
    db: Session = Depends(get_db),
    usuario_actual: Usuario = Depends(obtener_usuario_actual)
):
    """Agregar fragmento de práctica"""
    return crear_fragmento_practica(db, ejercicio_id, fragmento)

@router.get("/{ejercicio_id}/fragmentos", response_model=List[FragmentoPracticaResponse])
def listar_fragmentos_ejercicio(
    ejercicio_id: int,
    db: Session = Depends(get_db),
    usuario_actual: Usuario = Depends(obtener_usuario_actual)
):
    """Listar fragmentos de un ejercicio"""
    return obtener_fragmentos_ejercicio(db, ejercicio_id)