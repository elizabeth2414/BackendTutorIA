from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from typing import List, Optional

from app.modelos import EjercicioPractica, ResultadoEjercicio, FragmentoPractica
from app.esquemas.ejercicio import EjercicioPracticaCreate, EjercicioPracticaUpdate, ResultadoEjercicioCreate, FragmentoPracticaCreate

def crear_ejercicio(db: Session, ejercicio: EjercicioPracticaCreate):
    db_ejercicio = EjercicioPractica(**ejercicio.dict())
    db.add(db_ejercicio)
    db.commit()
    db.refresh(db_ejercicio)
    return db_ejercicio

def obtener_ejercicios(db: Session, skip: int = 0, limit: int = 100, 
                      estudiante_id: Optional[int] = None, evaluacion_id: Optional[int] = None,
                      completado: Optional[bool] = None):
    query = db.query(EjercicioPractica)
    if estudiante_id is not None:
        query = query.filter(EjercicioPractica.estudiante_id == estudiante_id)
    if evaluacion_id is not None:
        query = query.filter(EjercicioPractica.evaluacion_id == evaluacion_id)
    if completado is not None:
        query = query.filter(EjercicioPractica.completado == completado)
    return query.offset(skip).limit(limit).all()

def obtener_ejercicio(db: Session, ejercicio_id: int):
    return db.query(EjercicioPractica).filter(EjercicioPractica.id == ejercicio_id).first()

def actualizar_ejercicio(db: Session, ejercicio_id: int, ejercicio: EjercicioPracticaUpdate):
    db_ejercicio = obtener_ejercicio(db, ejercicio_id)
    if not db_ejercicio:
        raise HTTPException(status_code=404, detail="Ejercicio no encontrado")
    
    update_data = ejercicio.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_ejercicio, field, value)
    
    db.commit()
    db.refresh(db_ejercicio)
    return db_ejercicio

def eliminar_ejercicio(db: Session, ejercicio_id: int):
    db_ejercicio = obtener_ejercicio(db, ejercicio_id)
    if not db_ejercicio:
        raise HTTPException(status_code=404, detail="Ejercicio no encontrado")
    
    # Soft delete
    db_ejercicio.activo = False
    db.commit()
    return db_ejercicio

def crear_resultado_ejercicio(db: Session, ejercicio_id: int, resultado: ResultadoEjercicioCreate):
    db_resultado = ResultadoEjercicio(ejercicio_id=ejercicio_id, **resultado.dict())
    db.add(db_resultado)
    db.commit()
    db.refresh(db_resultado)
    return db_resultado

def obtener_resultados_ejercicio(db: Session, ejercicio_id: int):
    return db.query(ResultadoEjercicio).filter(ResultadoEjercicio.ejercicio_id == ejercicio_id).all()

def crear_fragmento_practica(db: Session, ejercicio_id: int, fragmento: FragmentoPracticaCreate):
    db_fragmento = FragmentoPractica(ejercicio_id=ejercicio_id, **fragmento.dict())
    db.add(db_fragmento)
    db.commit()
    db.refresh(db_fragmento)
    return db_fragmento

def obtener_fragmentos_ejercicio(db: Session, ejercicio_id: int):
    return db.query(FragmentoPractica).filter(FragmentoPractica.ejercicio_id == ejercicio_id).all()