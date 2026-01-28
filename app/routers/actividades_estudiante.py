from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List
from datetime import datetime

from app.config import get_db
from app.modelos import (
    Actividad, Pregunta, ProgresoActividad, 
    RespuestaPregunta, NivelEstudiante, Estudiante,
    HistorialPuntos
)
from app.servicios.seguridad import obtener_usuario_actual

router = APIRouter(prefix="/actividades", tags=["actividades-estudiante"])



class RespuestaRequest(BaseModel):
    pregunta_id: int
    respuesta_estudiante: str


class ResponderActividadRequest(BaseModel):
    estudiante_id: int
    actividad_id: int
    respuestas: List[RespuestaRequest]
    tiempo_total: int 


class ResponderActividadResponse(BaseModel):
    progreso_id: int
    puntos_obtenidos: int
    puntos_maximos: int
    respuestas_correctas: int
    respuestas_incorrectas: int
    porcentaje_acierto: float
    xp_ganado: int
    mensaje: str



@router.post("/responder", response_model=ResponderActividadResponse)
def responder_actividad(
    request: ResponderActividadRequest,
    db: Session = Depends(get_db)
):
    """
    Permite que un estudiante responda una actividad.
    - Califica automáticamente las respuestas
    - Calcula los puntos obtenidos
    - Suma XP a la aventura del estudiante
    - Actualiza el progreso
    """
    

    actividad = db.query(Actividad).filter(
        Actividad.id == request.actividad_id,
        Actividad.activo == True
    ).first()
    
    if not actividad:
        raise HTTPException(status_code=404, detail="Actividad no encontrada")
    
    
    estudiante = db.query(Estudiante).filter(
        Estudiante.id == request.estudiante_id
    ).first()
    
    if not estudiante:
        raise HTTPException(status_code=404, detail="Estudiante no encontrado")
    
  
    progreso = ProgresoActividad(
        estudiante_id=request.estudiante_id,
        actividad_id=request.actividad_id,
        fecha_completacion=datetime.now(),
        tiempo_completacion=request.tiempo_total,
        intentos=1,
        errores_cometidos=0,
        puntuacion=0.0  
    )
    db.add(progreso)
    db.flush()  
    
  
    puntos_totales = 0
    puntos_maximos = 0
    correctas = 0
    incorrectas = 0
    
    for resp in request.respuestas:
        # Obtener la pregunta
        pregunta = db.query(Pregunta).filter(
            Pregunta.id == resp.pregunta_id
        ).first()
        
        if not pregunta:
            continue
        
        puntos_maximos += pregunta.puntuacion
        
        
        es_correcta = False
        puntos_obtenidos = 0
        
       
        respuesta_estudiante = resp.respuesta_estudiante.strip().lower()
        respuesta_correcta = (pregunta.respuesta_correcta or "").strip().lower()
        
        if pregunta.tipo_respuesta == "multiple_choice":
            es_correcta = respuesta_estudiante == respuesta_correcta
        
        elif pregunta.tipo_respuesta == "verdadero_falso":
            es_correcta = respuesta_estudiante == respuesta_correcta
        
        elif pregunta.tipo_respuesta == "texto_libre":
       

            es_correcta = respuesta_estudiante in respuesta_correcta or respuesta_correcta in respuesta_estudiante
        
        if es_correcta:
            puntos_obtenidos = pregunta.puntuacion
            puntos_totales += puntos_obtenidos
            correctas += 1
        else:
            incorrectas += 1
        
        # Guardar la respuesta
        respuesta_db = RespuestaPregunta(
            progreso_id=progreso.id,
            pregunta_id=pregunta.id,
            respuesta_estudiante=resp.respuesta_estudiante,
            correcta=es_correcta,
            puntuacion_obtenida=puntos_obtenidos
        )
        db.add(respuesta_db)
    
  
    progreso.puntuacion = float(puntos_totales)
    progreso.errores_cometidos = incorrectas
    

    xp_ganado = puntos_totales * 10
    

    nivel = db.query(NivelEstudiante).filter(
        NivelEstudiante.estudiante_id == request.estudiante_id
    ).first()
    
    if not nivel:
       
        nivel = NivelEstudiante(
            estudiante_id=request.estudiante_id,
            nivel_actual=1,
            puntos_nivel_actual=0,
            puntos_para_siguiente_nivel=500,
            racha_actual=0
        )
        db.add(nivel)
        db.flush()
    
 
    nivel.puntos_nivel_actual += xp_ganado
    
    # Verificar si sube de nivel
    while nivel.puntos_nivel_actual >= nivel.puntos_para_siguiente_nivel:
        nivel.puntos_nivel_actual -= nivel.puntos_para_siguiente_nivel
        nivel.nivel_actual += 1
        nivel.puntos_para_siguiente_nivel = nivel.nivel_actual * 500
    
    
    historial = HistorialPuntos(
        estudiante_id=request.estudiante_id,
        puntos=xp_ganado,
        motivo=f"Actividad completada: {actividad.titulo}",
        fecha=datetime.now()
    )
    db.add(historial)
    
  
    db.commit()
    

    porcentaje = (puntos_totales / puntos_maximos * 100) if puntos_maximos > 0 else 0
    
    return ResponderActividadResponse(
        progreso_id=progreso.id,
        puntos_obtenidos=puntos_totales,
        puntos_maximos=puntos_maximos,
        respuestas_correctas=correctas,
        respuestas_incorrectas=incorrectas,
        porcentaje_acierto=round(porcentaje, 2),
        xp_ganado=xp_ganado,
        mensaje=f"¡Actividad completada! Has ganado {xp_ganado} XP"
    )



@router.get("/progreso/{progreso_id}")
def obtener_resultado_actividad(
    progreso_id: int,
    db: Session = Depends(get_db)
):
    """Obtener detalles del progreso de una actividad"""
    
    progreso = db.query(ProgresoActividad).filter(
        ProgresoActividad.id == progreso_id
    ).first()
    
    if not progreso:
        raise HTTPException(status_code=404, detail="Progreso no encontrado")
    
    # Obtener respuestas
    respuestas = db.query(RespuestaPregunta).filter(
        RespuestaPregunta.progreso_id == progreso_id
    ).all()
    
    return {
        "progreso_id": progreso.id,
        "estudiante_id": progreso.estudiante_id,
        "actividad_id": progreso.actividad_id,
        "puntuacion_obtenida": progreso.puntuacion,
        "fecha_completado": progreso.fecha_completacion,
        "tiempo_total": progreso.tiempo_completacion,
        "respuestas": [
            {
                "pregunta_id": r.pregunta_id,
                "respuesta_estudiante": r.respuesta_estudiante,
                "correcta": r.correcta,
                "puntuacion_obtenida": r.puntuacion_obtenida
            }
            for r in respuestas
        ]
    }



@router.get("/estudiante/{estudiante_id}/historial")
def obtener_historial_actividades(
    estudiante_id: int,
    db: Session = Depends(get_db)
):
    """Obtener todas las actividades completadas por un estudiante"""
    
    progresos = db.query(ProgresoActividad).filter(
        ProgresoActividad.estudiante_id == estudiante_id
    ).order_by(ProgresoActividad.fecha_completacion.desc()).all()
    
    return [
        {
            "progreso_id": p.id,
            "actividad_id": p.actividad_id,
            "actividad_titulo": p.actividad.titulo if p.actividad else "Sin título",
            "puntuacion_obtenida": p.puntuacion,
            "fecha_completado": p.fecha_completacion,
            "tiempo_total": p.tiempo_completacion
        }
        for p in progresos
    ]
