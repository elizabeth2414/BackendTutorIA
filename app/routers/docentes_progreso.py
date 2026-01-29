from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from typing import List, Optional
from datetime import datetime, timedelta

from app.config import get_db
from app.modelos import (
    Usuario, Docente, Estudiante, ProgresoActividad, 
    Actividad, EvaluacionLectura, ContenidoLectura,
    EstudianteCurso, Curso
)
from app.servicios.seguridad import obtener_usuario_actual

router = APIRouter(prefix="/docentes/progreso", tags=["Progreso Docentes"])


def obtener_o_crear_docente(db: Session, usuario_id: int):
    """Obtiene o crea el registro de docente para el usuario actual"""
    docente = db.query(Docente).filter(Docente.usuario_id == usuario_id).first()
    if not docente:
        docente = Docente(usuario_id=usuario_id, activo=True)
        db.add(docente)
        db.commit()
        db.refresh(docente)
    return docente


@router.get("/resumen")
def obtener_resumen_progreso_general(
    db: Session = Depends(get_db),
    usuario_actual: Usuario = Depends(obtener_usuario_actual)
):
    """
    Obtiene un resumen general del progreso de todos los estudiantes del docente.
    Incluye estadísticas globales y por estudiante.
    """
    docente = obtener_o_crear_docente(db, usuario_actual.id)
    
    # Obtener todos los estudiantes activos del docente
    estudiantes = (
        db.query(Estudiante)
        .filter(
            Estudiante.docente_id == docente.id,
            Estudiante.activo == True
        )
        .all()
    )
    
    if not estudiantes:
        return {
            "total_estudiantes": 0,
            "estudiantes": [],
            "estadisticas_generales": {
                "promedio_general": 0,
                "total_actividades_completadas": 0,
                "total_lecturas_completadas": 0
            }
        }
    
    estudiantes_ids = [e.id for e in estudiantes]
    
    # Estadísticas de actividades
    total_actividades = (
        db.query(func.count(ProgresoActividad.id))
        .filter(ProgresoActividad.estudiante_id.in_(estudiantes_ids))
        .scalar()
    ) or 0
    
    # Estadísticas de lecturas
    total_lecturas = (
        db.query(func.count(EvaluacionLectura.id.distinct()))
        .filter(
            EvaluacionLectura.estudiante_id.in_(estudiantes_ids),
            EvaluacionLectura.precision_palabras >= 70
        )
        .scalar()
    ) or 0
    
    # Promedio general de puntuaciones
    promedio_actividades = (
        db.query(func.avg(ProgresoActividad.puntuacion))
        .filter(ProgresoActividad.estudiante_id.in_(estudiantes_ids))
        .scalar()
    ) or 0
    
    promedio_lecturas = (
        db.query(func.avg(EvaluacionLectura.precision_palabras))
        .filter(
            EvaluacionLectura.estudiante_id.in_(estudiantes_ids),
            EvaluacionLectura.precision_palabras.isnot(None)
        )
        .scalar()
    ) or 0
    
    promedio_general = (promedio_actividades + promedio_lecturas) / 2 if (promedio_actividades or promedio_lecturas) else 0
    
    # Datos por estudiante
    estudiantes_data = []
    for est in estudiantes:
        # Actividades completadas
        actividades_count = (
            db.query(func.count(ProgresoActividad.id))
            .filter(ProgresoActividad.estudiante_id == est.id)
            .scalar()
        ) or 0
        
        # Lecturas completadas (con precisión >= 70%)
        lecturas_count = (
            db.query(func.count(EvaluacionLectura.contenido_id.distinct()))
            .filter(
                EvaluacionLectura.estudiante_id == est.id,
                EvaluacionLectura.precision_palabras >= 70
            )
            .scalar()
        ) or 0
        
        # Promedio de actividades
        promedio_act = (
            db.query(func.avg(ProgresoActividad.puntuacion))
            .filter(ProgresoActividad.estudiante_id == est.id)
            .scalar()
        ) or 0
        
        # Promedio de lecturas
        promedio_lec = (
            db.query(func.avg(EvaluacionLectura.precision_palabras))
            .filter(
                EvaluacionLectura.estudiante_id == est.id,
                EvaluacionLectura.precision_palabras.isnot(None)
            )
            .scalar()
        ) or 0
        
        # Promedio combinado
        promedio_estudiante = (promedio_act + promedio_lec) / 2 if (promedio_act or promedio_lec) else 0
        
        # Obtener curso
        curso_rel = (
            db.query(Curso.nombre)
            .join(EstudianteCurso, EstudianteCurso.curso_id == Curso.id)
            .filter(EstudianteCurso.estudiante_id == est.id)
            .first()
        )
        
        # Última actividad
        ultima_actividad = (
            db.query(ProgresoActividad.fecha_completacion)
            .filter(ProgresoActividad.estudiante_id == est.id)
            .order_by(desc(ProgresoActividad.fecha_completacion))
            .first()
        )
        
        ultima_lectura = (
            db.query(EvaluacionLectura.fecha_evaluacion)
            .filter(EvaluacionLectura.estudiante_id == est.id)
            .order_by(desc(EvaluacionLectura.fecha_evaluacion))
            .first()
        )
        
        # Determinar la última actividad más reciente
        ultima_fecha = None
        if ultima_actividad and ultima_lectura:
            ultima_fecha = max(ultima_actividad[0], ultima_lectura[0])
        elif ultima_actividad:
            ultima_fecha = ultima_actividad[0]
        elif ultima_lectura:
            ultima_fecha = ultima_lectura[0]
        
        estudiantes_data.append({
            "id": est.id,
            "nombre": est.nombre,
            "apellido": est.apellido,
            "nivel_educativo": est.nivel_educativo,
            "curso": curso_rel[0] if curso_rel else "Sin curso",
            "actividades_completadas": actividades_count,
            "lecturas_completadas": lecturas_count,
            "promedio": round(promedio_estudiante, 2),
            "ultima_actividad": ultima_fecha.isoformat() if ultima_fecha else None
        })
    
    return {
        "total_estudiantes": len(estudiantes),
        "estudiantes": estudiantes_data,
        "estadisticas_generales": {
            "promedio_general": round(promedio_general, 2),
            "total_actividades_completadas": total_actividades,
            "total_lecturas_completadas": total_lecturas
        }
    }


@router.get("/estudiante/{estudiante_id}")
def obtener_progreso_detallado_estudiante(
    estudiante_id: int,
    db: Session = Depends(get_db),
    usuario_actual: Usuario = Depends(obtener_usuario_actual)
):
    """
    Obtiene el progreso detallado de un estudiante específico.
    Solo accesible para el docente que registró al estudiante.
    """
    docente = obtener_o_crear_docente(db, usuario_actual.id)
    
    # Verificar que el estudiante pertenece al docente
    estudiante = (
        db.query(Estudiante)
        .filter(
            Estudiante.id == estudiante_id,
            Estudiante.docente_id == docente.id,
            Estudiante.activo == True
        )
        .first()
    )
    
    if not estudiante:
        raise HTTPException(
            status_code=403,
            detail="No tienes permiso para ver el progreso de este estudiante o el estudiante no existe."
        )
    
    # Información básica del estudiante
    curso_rel = (
        db.query(Curso)
        .join(EstudianteCurso, EstudianteCurso.curso_id == Curso.id)
        .filter(EstudianteCurso.estudiante_id == estudiante_id)
        .first()
    )
    
    # Actividades completadas con detalles
    actividades = (
        db.query(
            ProgresoActividad.id,
            ProgresoActividad.puntuacion,
            ProgresoActividad.fecha_completacion,
            ProgresoActividad.tiempo_completacion,
            ProgresoActividad.intentos,
            Actividad.titulo,
            Actividad.tipo,
            Actividad.puntos_maximos
        )
        .join(Actividad, Actividad.id == ProgresoActividad.actividad_id)
        .filter(ProgresoActividad.estudiante_id == estudiante_id)
        .order_by(desc(ProgresoActividad.fecha_completacion))
        .all()
    )
    
    actividades_data = [
        {
            "id": a.id,
            "titulo": a.titulo,
            "tipo": a.tipo,
            "puntuacion": round(a.puntuacion, 2),
            "puntos_maximos": a.puntos_maximos,
            "fecha_completacion": a.fecha_completacion.isoformat(),
            "tiempo_completacion": a.tiempo_completacion,
            "intentos": a.intentos
        }
        for a in actividades
    ]
    
    # Lecturas evaluadas con detalles
    lecturas = (
        db.query(
            EvaluacionLectura.id,
            EvaluacionLectura.precision_palabras,
            EvaluacionLectura.velocidad_lectura,
            EvaluacionLectura.fluidez,
            EvaluacionLectura.fecha_evaluacion,
            EvaluacionLectura.retroalimentacion_ia,
            ContenidoLectura.titulo
        )
        .join(ContenidoLectura, ContenidoLectura.id == EvaluacionLectura.contenido_id)
        .filter(EvaluacionLectura.estudiante_id == estudiante_id)
        .order_by(desc(EvaluacionLectura.fecha_evaluacion))
        .all()
    )
    
    lecturas_data = [
        {
            "id": l.id,
            "titulo": l.titulo,
            "precision_palabras": round(l.precision_palabras, 2) if l.precision_palabras else None,
            "velocidad_lectura": round(l.velocidad_lectura, 2) if l.velocidad_lectura else None,
            "fluidez": round(l.fluidez, 2) if l.fluidez else None,
            "fecha_evaluacion": l.fecha_evaluacion.isoformat(),
            "retroalimentacion": l.retroalimentacion_ia,
            "aprobada": l.precision_palabras >= 70 if l.precision_palabras else False
        }
        for l in lecturas
    ]
    
    # Estadísticas del estudiante
    promedio_actividades = (
        db.query(func.avg(ProgresoActividad.puntuacion))
        .filter(ProgresoActividad.estudiante_id == estudiante_id)
        .scalar()
    ) or 0
    
    promedio_lecturas = (
        db.query(func.avg(EvaluacionLectura.precision_palabras))
        .filter(
            EvaluacionLectura.estudiante_id == estudiante_id,
            EvaluacionLectura.precision_palabras.isnot(None)
        )
        .scalar()
    ) or 0
    
    # Progreso semanal (últimos 7 días)
    hace_7_dias = datetime.now() - timedelta(days=7)
    
    actividades_semana = (
        db.query(func.count(ProgresoActividad.id))
        .filter(
            ProgresoActividad.estudiante_id == estudiante_id,
            ProgresoActividad.fecha_completacion >= hace_7_dias
        )
        .scalar()
    ) or 0
    
    lecturas_semana = (
        db.query(func.count(EvaluacionLectura.id))
        .filter(
            EvaluacionLectura.estudiante_id == estudiante_id,
            EvaluacionLectura.fecha_evaluacion >= hace_7_dias
        )
        .scalar()
    ) or 0
    
    return {
        "estudiante": {
            "id": estudiante.id,
            "nombre": estudiante.nombre,
            "apellido": estudiante.apellido,
            "nivel_educativo": estudiante.nivel_educativo,
            "curso": curso_rel.nombre if curso_rel else "Sin curso",
            "fecha_nacimiento": estudiante.fecha_nacimiento.isoformat()
        },
        "estadisticas": {
            "total_actividades": len(actividades_data),
            "total_lecturas": len(lecturas_data),
            "promedio_actividades": round(promedio_actividades, 2),
            "promedio_lecturas": round(promedio_lecturas, 2),
            "promedio_general": round((promedio_actividades + promedio_lecturas) / 2, 2) if (promedio_actividades or promedio_lecturas) else 0,
            "actividades_esta_semana": actividades_semana,
            "lecturas_esta_semana": lecturas_semana
        },
        "actividades": actividades_data,
        "lecturas": lecturas_data
    }


@router.get("/estudiante/{estudiante_id}/grafica-progreso")
def obtener_grafica_progreso(
    estudiante_id: int,
    periodo: str = "mes",  # "semana", "mes", "trimestre"
    db: Session = Depends(get_db),
    usuario_actual: Usuario = Depends(obtener_usuario_actual)
):
    """
    Obtiene datos para graficar el progreso del estudiante en el tiempo.
    Solo accesible para el docente que registró al estudiante.
    """
    docente = obtener_o_crear_docente(db, usuario_actual.id)
    
    # Verificar que el estudiante pertenece al docente
    estudiante = (
        db.query(Estudiante)
        .filter(
            Estudiante.id == estudiante_id,
            Estudiante.docente_id == docente.id,
            Estudiante.activo == True
        )
        .first()
    )
    
    if not estudiante:
        raise HTTPException(
            status_code=403,
            detail="No tienes permiso para ver el progreso de este estudiante."
        )
    
    # Determinar el rango de fechas según el período
    ahora = datetime.now()
    if periodo == "semana":
        fecha_inicio = ahora - timedelta(days=7)
    elif periodo == "trimestre":
        fecha_inicio = ahora - timedelta(days=90)
    else:  # mes por defecto
        fecha_inicio = ahora - timedelta(days=30)
    
    # Obtener actividades en el período
    actividades = (
        db.query(
            func.date(ProgresoActividad.fecha_completacion).label('fecha'),
            func.avg(ProgresoActividad.puntuacion).label('promedio')
        )
        .filter(
            ProgresoActividad.estudiante_id == estudiante_id,
            ProgresoActividad.fecha_completacion >= fecha_inicio
        )
        .group_by(func.date(ProgresoActividad.fecha_completacion))
        .order_by(func.date(ProgresoActividad.fecha_completacion))
        .all()
    )
    
    # Obtener lecturas en el período
    lecturas = (
        db.query(
            func.date(EvaluacionLectura.fecha_evaluacion).label('fecha'),
            func.avg(EvaluacionLectura.precision_palabras).label('promedio')
        )
        .filter(
            EvaluacionLectura.estudiante_id == estudiante_id,
            EvaluacionLectura.fecha_evaluacion >= fecha_inicio,
            EvaluacionLectura.precision_palabras.isnot(None)
        )
        .group_by(func.date(EvaluacionLectura.fecha_evaluacion))
        .order_by(func.date(EvaluacionLectura.fecha_evaluacion))
        .all()
    )
    
    return {
        "periodo": periodo,
        "fecha_inicio": fecha_inicio.isoformat(),
        "fecha_fin": ahora.isoformat(),
        "actividades": [
            {
                "fecha": a.fecha.isoformat(),
                "promedio": round(a.promedio, 2)
            }
            for a in actividades
        ],
        "lecturas": [
            {
                "fecha": l.fecha.isoformat(),
                "promedio": round(l.promedio, 2)
            }
            for l in lecturas
        ]
    }