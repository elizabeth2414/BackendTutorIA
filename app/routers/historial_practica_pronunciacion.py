from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime
import json

from app.config import get_db
from app.servicios.seguridad import obtener_usuario_actual
from app.modelos import Usuario, Estudiante, Padre, EjercicioPractica, EvaluacionLectura

router = APIRouter(
    prefix="/historial/practicas",
    tags=["Historial Prácticas Pronunciación"]
)


# =========================================================
# ESTUDIANTE: ver sus prácticas
# =========================================================
@router.get("/mis")
def obtener_mis_practicas(
    db: Session = Depends(get_db),
    usuario_actual: Usuario = Depends(obtener_usuario_actual)
):
    """
    ✅ ACTUALIZADO: Consulta ejercicio_practica en lugar de historial_practica_pronunciacion
    """
    estudiante = (
        db.query(Estudiante)
        .filter(Estudiante.usuario_id == usuario_actual.id)
        .first()
    )

    if not estudiante:
        raise HTTPException(404, "Estudiante no encontrado")

    # 🔥 CONSULTAR EJERCICIOS REALES
    ejercicios = (
        db.query(EjercicioPractica)
        .filter(EjercicioPractica.estudiante_id == estudiante.id)
        .order_by(EjercicioPractica.fecha_creacion.desc())  # ✅ CAMPO CORRECTO
        .all()
    )

    # Formatear respuesta compatible con el frontend
    historial = []
    for ej in ejercicios:
        # Manejar palabras_objetivo (puede ser None, lista, o string JSON)
        num_errores = 0
        if ej.palabras_objetivo:
            if isinstance(ej.palabras_objetivo, list):
                num_errores = len(ej.palabras_objetivo)
            elif isinstance(ej.palabras_objetivo, str):
                try:
                    palabras = json.loads(ej.palabras_objetivo)
                    num_errores = len(palabras) if isinstance(palabras, list) else 0
                except:
                    num_errores = 0
        
        # Calcular puntuación basada en completado
        puntuacion = 100 if ej.completado else 50
        
        historial.append({
            "id": ej.id,
            "estudiante_id": ej.estudiante_id,
            "fecha": ej.fecha_creacion.isoformat() if ej.fecha_creacion else datetime.now().isoformat(),  # ✅ CAMPO CORRECTO
            "puntuacion": puntuacion,
            "errores_detectados": num_errores,
            "errores_corregidos": 1 if ej.completado else 0,
            "tiempo_practica": ej.intentos * 60 if ej.intentos else 0,  # Estimado
            "tipo_ejercicio": ej.tipo_ejercicio or "pronunciacion",
            "completado": ej.completado,
            "intentos": ej.intentos or 0,
            "dificultad": ej.dificultad or 2
        })

    return historial


# =========================================================
# PADRE: ver prácticas de un hijo
# =========================================================
@router.get("/hijo/{estudiante_id}")
def obtener_practicas_hijo(
    estudiante_id: int,
    db: Session = Depends(get_db),
    usuario_actual: Usuario = Depends(obtener_usuario_actual)
):
    """
    ✅ ACTUALIZADO: Consulta ejercicio_practica en lugar de historial_practica_pronunciacion
    """
    padre = (
        db.query(Padre)
        .filter(Padre.usuario_id == usuario_actual.id)
        .first()
    )

    if not padre:
        raise HTTPException(403, "Acceso solo para padres")

    estudiante = (
        db.query(Estudiante)
        .filter(
            Estudiante.id == estudiante_id,
            Estudiante.padre_id == padre.id
        )
        .first()
    )

    if not estudiante:
        raise HTTPException(403, "No autorizado")

    # 🔥 CONSULTAR EJERCICIOS REALES
    ejercicios = (
        db.query(EjercicioPractica)
        .filter(EjercicioPractica.estudiante_id == estudiante.id)
        .order_by(EjercicioPractica.fecha_creacion.desc())  # ✅ CAMPO CORRECTO
        .all()
    )

    # Formatear respuesta compatible con el frontend
    historial = []
    for ej in ejercicios:
        # Manejar palabras_objetivo (puede ser None, lista, o string JSON)
        num_errores = 0
        if ej.palabras_objetivo:
            if isinstance(ej.palabras_objetivo, list):
                num_errores = len(ej.palabras_objetivo)
            elif isinstance(ej.palabras_objetivo, str):
                try:
                    palabras = json.loads(ej.palabras_objetivo)
                    num_errores = len(palabras) if isinstance(palabras, list) else 0
                except:
                    num_errores = 0
        
        # Calcular puntuación basada en completado
        puntuacion = 100 if ej.completado else 50
        
        historial.append({
            "id": ej.id,
            "estudiante_id": ej.estudiante_id,
            "fecha": ej.fecha_creacion.isoformat() if ej.fecha_creacion else datetime.now().isoformat(),  # ✅ CAMPO CORRECTO
            "puntuacion": puntuacion,
            "errores_detectados": num_errores,
            "errores_corregidos": 1 if ej.completado else 0,
            "tiempo_practica": ej.intentos * 60 if ej.intentos else 0,  # Estimado
            "tipo_ejercicio": ej.tipo_ejercicio or "pronunciacion",
            "completado": ej.completado,
            "intentos": ej.intentos or 0,
            "dificultad": ej.dificultad or 2
        })

    return historial
