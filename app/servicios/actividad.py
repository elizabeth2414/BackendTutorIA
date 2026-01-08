from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from typing import List, Optional

from app.modelos import Actividad, Pregunta, ProgresoActividad, RespuestaPregunta
from app.esquemas.actividad import ActividadCreate, ActividadUpdate, PreguntaCreate, ProgresoActividadCreate, RespuestaPreguntaCreate

def crear_actividad(db: Session, actividad: ActividadCreate):
    db_actividad = Actividad(**actividad.dict())
    db.add(db_actividad)
    db.commit()
    db.refresh(db_actividad)
    return db_actividad

def obtener_actividades(db: Session, skip: int = 0, limit: int = 100, 
                       contenido_id: Optional[int] = None, activo: Optional[bool] = None):
    query = db.query(Actividad)
    if contenido_id is not None:
        query = query.filter(Actividad.contenido_id == contenido_id)
    if activo is not None:
        query = query.filter(Actividad.activo == activo)
    return query.offset(skip).limit(limit).all()

def obtener_actividad(db: Session, actividad_id: int):
    return db.query(Actividad).filter(Actividad.id == actividad_id).first()

def actualizar_actividad(db: Session, actividad_id: int, actividad: ActividadUpdate):
    db_actividad = obtener_actividad(db, actividad_id)
    if not db_actividad:
        raise HTTPException(status_code=404, detail="Actividad no encontrada")
    
    update_data = actividad.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_actividad, field, value)
    
    db.commit()
    db.refresh(db_actividad)
    return db_actividad

def eliminar_actividad(db: Session, actividad_id: int):
    db_actividad = obtener_actividad(db, actividad_id)
    if not db_actividad:
        raise HTTPException(status_code=404, detail="Actividad no encontrada")
    
    # Soft delete
    db_actividad.activo = False
    db.commit()
    return db_actividad

def crear_pregunta(db: Session, actividad_id: int, pregunta: PreguntaCreate):
    db_pregunta = Pregunta(actividad_id=actividad_id, **pregunta.dict())
    db.add(db_pregunta)
    db.commit()
    db.refresh(db_pregunta)
    return db_pregunta

def obtener_preguntas_actividad(db: Session, actividad_id: int):
    return db.query(Pregunta).filter(Pregunta.actividad_id == actividad_id).all()

def crear_progreso_actividad(db: Session, progreso: ProgresoActividadCreate):
    db_progreso = ProgresoActividad(**progreso.dict())
    db.add(db_progreso)
    db.commit()
    db.refresh(db_progreso)
    return db_progreso

def obtener_progreso_estudiante(db: Session, estudiante_id: int):
    return db.query(ProgresoActividad).filter(ProgresoActividad.estudiante_id == estudiante_id).all()

def crear_respuesta_pregunta(db: Session, progreso_id: int, respuesta: RespuestaPreguntaCreate):
    db_respuesta = RespuestaPregunta(progreso_id=progreso_id, **respuesta.dict())
    db.add(db_respuesta)
    db.commit()
    db.refresh(db_respuesta)
    return db_respuesta

def obtener_respuestas_progreso(db: Session, progreso_id: int):
    return db.query(RespuestaPregunta).filter(RespuestaPregunta.progreso_id == progreso_id).all()