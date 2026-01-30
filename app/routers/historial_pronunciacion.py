from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime

from app.config import get_db
from app.servicios.seguridad import obtener_usuario_actual, obtener_docente_actual
from app.modelos import Usuario, Estudiante, Padre, Docente, EvaluacionLectura, ContenidoLectura

router = APIRouter(
    prefix="/historial/pronunciacion",
    tags=["Historial Pronunciación"]
)



@router.get("/mis")
def obtener_mi_historial_pronunciacion(
    db: Session = Depends(get_db),
    usuario_actual: Usuario = Depends(obtener_usuario_actual)
):
    """
    ACTUALIZADO: Consulta evaluacion_lectura en lugar de historial_pronunciacion
    """
    estudiante = (
        db.query(Estudiante)
        .filter(Estudiante.usuario_id == usuario_actual.id)
        .first()
    )

    if not estudiante:
        raise HTTPException(404, "Estudiante no encontrado")

  
    evaluaciones = (
        db.query(EvaluacionLectura)
        .filter(EvaluacionLectura.estudiante_id == estudiante.id)
        .order_by(EvaluacionLectura.fecha_evaluacion.desc())
        .all()
    )

    
    historial = []
    for ev in evaluaciones:
        
        contenido = db.query(ContenidoLectura).filter(
            ContenidoLectura.id == ev.contenido_id
        ).first()

        historial.append({
            "id": ev.id,
            "estudiante_id": ev.estudiante_id,
            "lectura_titulo": contenido.titulo if contenido else "Sin título",
            "lectura_id": ev.contenido_id,
            "fecha": ev.fecha_evaluacion.isoformat() if ev.fecha_evaluacion else datetime.now().isoformat(),
            "puntuacion_global": round(ev.precision_palabras or 0, 1),
            "fluidez": round(ev.puntuacion_pronunciacion or 0, 1),
            "velocidad": round(ev.velocidad_lectura or 0, 1),
            "palabras_por_minuto": round(ev.velocidad_lectura or 0, 1),
            "precision": round(ev.precision_palabras or 0, 1),
            "retroalimentacion": ev.retroalimentacion_ia or "",
            "audio_url": ev.audio_url,
            "duracion_audio": ev.duracion_audio,
        })

    return historial



@router.get("/hijo/{estudiante_id}")
def obtener_historial_pronunciacion_hijo(
    estudiante_id: int,
    db: Session = Depends(get_db),
    usuario_actual: Usuario = Depends(obtener_usuario_actual)
):
    """
    ACTUALIZADO: Consulta evaluacion_lectura en lugar de historial_pronunciacion
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
        raise HTTPException(403, "No autorizado para ver este estudiante")

   
    evaluaciones = (
        db.query(EvaluacionLectura)
        .filter(EvaluacionLectura.estudiante_id == estudiante.id)
        .order_by(EvaluacionLectura.fecha_evaluacion.desc())
        .all()
    )

   
    historial = []
    for ev in evaluaciones:
        
        contenido = db.query(ContenidoLectura).filter(
            ContenidoLectura.id == ev.contenido_id
        ).first()

        historial.append({
            "id": ev.id,
            "estudiante_id": ev.estudiante_id,
            "lectura_titulo": contenido.titulo if contenido else "Sin título",
            "lectura_id": ev.contenido_id,
            "fecha": ev.fecha_evaluacion.isoformat() if ev.fecha_evaluacion else datetime.now().isoformat(),
            "puntuacion_global": round(ev.precision_palabras or 0, 1),
            "fluidez": round(ev.puntuacion_pronunciacion or 0, 1),
            "velocidad": round(ev.velocidad_lectura or 0, 1),
            "palabras_por_minuto": round(ev.velocidad_lectura or 0, 1),
            "precision": round(ev.precision_palabras or 0, 1),
            "retroalimentacion": ev.retroalimentacion_ia or "",
            "audio_url": ev.audio_url,
            "duracion_audio": ev.duracion_audio,
        })

    return historial



@router.get("/docente/{estudiante_id}")
@router.get("/estudiante/{estudiante_id}")
def obtener_historial_pronunciacion_estudiante_docente(
    estudiante_id: int,
    db: Session = Depends(get_db),
    docente: Docente = Depends(obtener_docente_actual),
):
    """Historial de pronunciación de un estudiante (vista docente)."""
    estudiante = (
        db.query(Estudiante)
        .filter(
            Estudiante.id == estudiante_id,
            Estudiante.docente_id == docente.id,
        )
        .first()
    )

    if not estudiante:
        raise HTTPException(403, "No autorizado para ver este estudiante")

    evaluaciones = (
        db.query(EvaluacionLectura)
        .filter(EvaluacionLectura.estudiante_id == estudiante.id)
        .order_by(EvaluacionLectura.fecha_evaluacion.desc())
        .all()
    )

    historial = []
    for ev in evaluaciones:
        contenido = db.query(ContenidoLectura).filter(
            ContenidoLectura.id == ev.contenido_id
        ).first()

        historial.append({
            "id": ev.id,
            "estudiante_id": ev.estudiante_id,
            "lectura_titulo": contenido.titulo if contenido else "Sin título",
            "lectura_id": ev.contenido_id,
            "fecha": ev.fecha_evaluacion.isoformat() if ev.fecha_evaluacion else datetime.now().isoformat(),
            "puntuacion_global": round(ev.precision_palabras or 0, 1),
            "fluidez": round(ev.puntuacion_pronunciacion or 0, 1),
            "velocidad": round(ev.velocidad_lectura or 0, 1),
            "palabras_por_minuto": round(ev.velocidad_lectura or 0, 1),
            "precision": round(ev.precision_palabras or 0, 1),
            "retroalimentacion": ev.retroalimentacion_ia or "",
            "audio_url": ev.audio_url,
            "duracion_audio": ev.duracion_audio,
        })

    return historial
