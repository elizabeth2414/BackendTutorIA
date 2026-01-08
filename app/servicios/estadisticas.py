from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from datetime import datetime, timedelta
from typing import List

from app.modelos import Estudiante, Curso, EvaluacionLectura, ProgresoActividad, NivelEstudiante, RecompensaEstudiante
from app.esquemas.estadisticas import EstadisticasEstudiante, ProgresoCurso, ReporteEvaluacion, TendenciaProgreso, DashboardDocente

def obtener_estadisticas_estudiante(db: Session, estudiante_id: int):
    # Obtener el nivel del estudiante
    nivel = db.query(NivelEstudiante).filter(NivelEstudiante.estudiante_id == estudiante_id).first()
    if not nivel:
        raise HTTPException(status_code=404, detail="Estudiante no encontrado")
    
    # Obtener cantidad de recompensas
    recompensas = db.query(RecompensaEstudiante).filter(
        RecompensaEstudiante.estudiante_id == estudiante_id
    ).count()
    
    # Calcular progreso en el nivel actual
    progreso_nivel = (nivel.puntos_nivel_actual / nivel.puntos_para_siguiente_nivel) * 100 if nivel.puntos_para_siguiente_nivel > 0 else 0
    
    return EstadisticasEstudiante(
        estudiante_id=estudiante_id,
        nivel_actual=nivel.nivel_actual,
        puntos_totales=nivel.puntos_totales,
        lecturas_completadas=nivel.lecturas_completadas,
        actividades_completadas=nivel.actividades_completadas,
        racha_actual=nivel.racha_actual,
        racha_maxima=nivel.racha_maxima,
        progreso_nivel=progreso_nivel,
        recompensas_obtenidas=recompensas
    )

def obtener_progreso_cursos(db: Session, docente_id: int):
    # Obtener cursos del docente
    from app.modelos import EstudianteCurso, ContenidoLectura
    cursos = db.query(Curso).filter(Curso.docente_id == docente_id).all()
    
    resultados = []
    for curso in cursos:
        # Contar estudiantes activos en el curso
        total_estudiantes = db.query(EstudianteCurso).filter(
            EstudianteCurso.curso_id == curso.id,
            EstudianteCurso.estado == 'activo'
        ).count()
        
        # Obtener nivel promedio de los estudiantes
        nivel_promedio = db.query(func.avg(NivelEstudiante.nivel_actual)).join(
            Estudiante
        ).join(EstudianteCurso).filter(
            EstudianteCurso.curso_id == curso.id,
            EstudianteCurso.estado == 'activo'
        ).scalar() or 0
        
        # Contar lecturas del curso
        total_lecturas = db.query(ContenidoLectura).filter(ContenidoLectura.curso_id == curso.id).count()
        
        resultados.append(ProgresoCurso(
            curso_id=curso.id,
            curso_nombre=curso.nombre,
            total_estudiantes=total_estudiantes,
            nivel_promedio=round(nivel_promedio, 2),
            total_lecturas=total_lecturas
        ))
    
    return resultados

def obtener_reportes_evaluacion(db: Session, estudiante_id: int, limite: int = 10):
    evaluaciones = db.query(EvaluacionLectura).filter(
        EvaluacionLectura.estudiante_id == estudiante_id
    ).order_by(EvaluacionLectura.fecha_evaluacion.desc()).limit(limite).all()
    
    reportes = []
    for eval in evaluaciones:
        # Obtener análisis IA para palabras por minuto
        from app.modelos import AnalisisIA
        analisis = db.query(AnalisisIA).filter(AnalisisIA.evaluacion_id == eval.id).first()
        ppm = analisis.palabras_por_minuto if analisis else 0
        
        reportes.append(ReporteEvaluacion(
            evaluacion_id=eval.id,
            fecha_evaluacion=eval.fecha_evaluacion,
            puntuacion_pronunciacion=eval.puntuacion_pronunciacion or 0,
            velocidad_lectura=eval.velocidad_lectura or 0,
            fluidez=eval.fluidez or 0,
            precision_palabras=eval.precision_palabras or 0,
            palabras_por_minuto=ppm
        ))
    
    return reportes

def obtener_tendencias_progreso(db: Session, estudiante_id: int, dias: int = 30):
    fecha_inicio = datetime.now() - timedelta(days=dias)
    
    # Obtener evaluaciones en el rango de fechas
    evaluaciones = db.query(EvaluacionLectura).filter(
        EvaluacionLectura.estudiante_id == estudiante_id,
        EvaluacionLectura.fecha_evaluacion >= fecha_inicio
    ).all()
    
    # Agrupar por fecha y calcular promedios
    tendencias = []
    for i in range(dias):
        fecha = (datetime.now() - timedelta(days=i)).date()
        eval_dia = [e for e in evaluaciones if e.fecha_evaluacion.date() == fecha]
        
        puntuacion_promedio = sum(e.puntuacion_pronunciacion or 0 for e in eval_dia) / len(eval_dia) if eval_dia else 0
        lecturas_completadas = len(eval_dia)
        
        # Obtener actividades completadas
        actividades_completadas = db.query(ProgresoActividad).filter(
            ProgresoActividad.estudiante_id == estudiante_id,
            func.date(ProgresoActividad.fecha_completacion) == fecha
        ).count()
        
        tendencias.append(TendenciaProgreso(
            fecha=fecha,
            puntuacion_promedio=round(puntuacion_promedio, 2),
            lecturas_completadas=lecturas_completadas,
            actividades_completadas=actividades_completadas
        ))
    
    return tendencias[::-1]  # Ordenar de más antiguo a más reciente

def obtener_dashboard_docente(db: Session, docente_id: int):
    # Obtener cursos del docente
    from app.modelos import EstudianteCurso, ContenidoLectura
    cursos = db.query(Curso).filter(Curso.docente_id == docente_id).all()
    
    total_estudiantes = 0
    total_lecturas = 0
    total_evaluaciones = 0
    estudiantes_activos = 0
    
    for curso in cursos:
        # Estudiantes por curso
        estudiantes_curso = db.query(EstudianteCurso).filter(EstudianteCurso.curso_id == curso.id).count()
        total_estudiantes += estudiantes_curso
        
        # Estudiantes activos
        activos_curso = db.query(EstudianteCurso).filter(
            EstudianteCurso.curso_id == curso.id,
            EstudianteCurso.estado == 'activo'
        ).count()
        estudiantes_activos += activos_curso
        
        # Lecturas del curso
        lecturas_curso = db.query(ContenidoLectura).filter(ContenidoLectura.curso_id == curso.id).count()
        total_lecturas += lecturas_curso
        
        # Evaluaciones de los estudiantes del curso
        eval_curso = db.query(EvaluacionLectura).join(Estudiante).join(EstudianteCurso).filter(
            EstudianteCurso.curso_id == curso.id
        ).count()
        total_evaluaciones += eval_curso
    
    # Obtener tendencias de progreso (últimos 7 días)
    tendencias = obtener_tendencias_progreso_docente(db, docente_id, 7)
    
    return DashboardDocente(
        total_estudiantes=total_estudiantes,
        total_cursos=len(cursos),
        total_lecturas=total_lecturas,
        total_evaluaciones=total_evaluaciones,
        estudiantes_activos=estudiantes_activos,
        progreso_promedio=0,  # Se calcularía basado en el progreso real
        tendencia_progreso=tendencias
    )

def obtener_tendencias_progreso_docente(db: Session, docente_id: int, dias: int):
    # Obtener todos los estudiantes de los cursos del docente
    from app.modelos import EstudianteCurso
    estudiantes = db.query(Estudiante.id).join(EstudianteCurso).join(Curso).filter(
        Curso.docente_id == docente_id
    ).all()
    estudiante_ids = [e.id for e in estudiantes]
    
    tendencias = []
    for i in range(dias):
        fecha = (datetime.now() - timedelta(days=i)).date()
        
        # Evaluaciones de ese día
        evaluaciones = db.query(EvaluacionLectura).filter(
            EvaluacionLectura.estudiante_id.in_(estudiante_ids),
            func.date(EvaluacionLectura.fecha_evaluacion) == fecha
        ).all()
        
        puntuacion_promedio = sum(e.puntuacion_pronunciacion or 0 for e in evaluaciones) / len(evaluaciones) if evaluaciones else 0
        lecturas_completadas = len(evaluaciones)
        
        # Actividades completadas
        actividades_completadas = db.query(ProgresoActividad).filter(
            ProgresoActividad.estudiante_id.in_(estudiante_ids),
            func.date(ProgresoActividad.fecha_completacion) == fecha
        ).count()
        
        tendencias.append(TendenciaProgreso(
            fecha=fecha,
            puntuacion_promedio=round(puntuacion_promedio, 2),
            lecturas_completadas=lecturas_completadas,
            actividades_completadas=actividades_completadas
        ))
    
    return tendencias[::-1]