from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from typing import List, Optional

from app.modelos import EvaluacionLectura, AnalisisIA, IntentoLectura, DetalleEvaluacion, ErrorPronunciacion
from app.esquemas.evaluacion import EvaluacionLecturaCreate, AnalisisIACreate, IntentoLecturaCreate, DetalleEvaluacionCreate, ErrorPronunciacionCreate

def crear_evaluacion(db: Session, evaluacion: EvaluacionLecturaCreate):
    db_evaluacion = EvaluacionLectura(**evaluacion.dict())
    db.add(db_evaluacion)
    db.commit()
    db.refresh(db_evaluacion)
    return db_evaluacion

def obtener_evaluaciones(db: Session, skip: int = 0, limit: int = 100, 
                        estudiante_id: Optional[int] = None, contenido_id: Optional[int] = None):
    query = db.query(EvaluacionLectura)
    if estudiante_id is not None:
        query = query.filter(EvaluacionLectura.estudiante_id == estudiante_id)
    if contenido_id is not None:
        query = query.filter(EvaluacionLectura.contenido_id == contenido_id)
    return query.offset(skip).limit(limit).all()

def obtener_evaluacion(db: Session, evaluacion_id: int):
    return db.query(EvaluacionLectura).filter(EvaluacionLectura.id == evaluacion_id).first()

def crear_analisis_ia(db: Session, evaluacion_id: int, analisis: AnalisisIACreate):
    db_analisis = AnalisisIA(evaluacion_id=evaluacion_id, **analisis.dict())
    db.add(db_analisis)
    db.commit()
    db.refresh(db_analisis)
    return db_analisis

def obtener_analisis_evaluacion(db: Session, evaluacion_id: int):
    return db.query(AnalisisIA).filter(AnalisisIA.evaluacion_id == evaluacion_id).first()

def crear_intento_lectura(db: Session, evaluacion_id: int, intento: IntentoLecturaCreate):
    db_intento = IntentoLectura(evaluacion_id=evaluacion_id, **intento.dict())
    db.add(db_intento)
    db.commit()
    db.refresh(db_intento)
    return db_intento

def obtener_intentos_evaluacion(db: Session, evaluacion_id: int):
    return db.query(IntentoLectura).filter(IntentoLectura.evaluacion_id == evaluacion_id).all()

def crear_detalle_evaluacion(db: Session, evaluacion_id: int, detalle: DetalleEvaluacionCreate):
    db_detalle = DetalleEvaluacion(evaluacion_id=evaluacion_id, **detalle.dict())
    db.add(db_detalle)
    db.commit()
    db.refresh(db_detalle)
    return db_detalle

def obtener_detalles_evaluacion(db: Session, evaluacion_id: int):
    return db.query(DetalleEvaluacion).filter(DetalleEvaluacion.evaluacion_id == evaluacion_id).all()

def crear_error_pronunciacion(db: Session, detalle_id: int, error: ErrorPronunciacionCreate):
    db_error = ErrorPronunciacion(detalle_evaluacion_id=detalle_id, **error.dict())
    db.add(db_error)
    db.commit()
    db.refresh(db_error)
    return db_error