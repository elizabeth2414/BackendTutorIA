# app/routers/ia_actividades.py

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.config import get_db
from app.modelos import ContenidoLectura, Actividad, Usuario
from app.servicios.seguridad import obtener_usuario_actual
from app.servicios.ia_actividades import generar_actividad_ia_para_contenido
from app.esquemas.actividad_ia import (
    GenerarActividadesIARequest,
    GenerarActividadesIAResponse,
    ActividadResponse,
    ActividadBase
)

router = APIRouter(prefix="/ia", tags=["ia-actividades"])



@router.post(
    "/lecturas/{contenido_id}/generar-actividades",
    response_model=GenerarActividadesIAResponse
)
def generar_actividades_ia(
    contenido_id: int,
    opciones: GenerarActividadesIARequest,
    db: Session = Depends(get_db),
    usuario_actual: Usuario = Depends(obtener_usuario_actual)
):

    contenido = (
        db.query(ContenidoLectura)
        .filter(
            ContenidoLectura.id == contenido_id,
            ContenidoLectura.activo == True
        )
        .first()
    )

    if not contenido:
        raise HTTPException(status_code=404, detail="Contenido de lectura no encontrado")

    # (Opcional) Validar que sea del docente dueño
    # if contenido.docente_id != usuario_actual.docente.id:
    #     raise HTTPException(status_code=403, detail="No autorizado")

    try:
        actividad = generar_actividad_ia_para_contenido(db, contenido, opciones)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        # Capturar cualquier otro error inesperado
        raise HTTPException(status_code=500, detail=f"Error generando actividad: {str(e)}")

    # 🔥 CAMBIO AQUÍ: Pydantic lo convierte automáticamente
    return GenerarActividadesIAResponse(
        contenido_id=contenido.id,
        actividad_id=actividad.id,
        total_preguntas=len(actividad.preguntas),
        mensaje="Actividad generada correctamente por IA.",
        actividad=actividad  # ✅ Pasa el objeto directamente, NO uses .from_attributes()
    )


# =====================================================
# 2️⃣ LISTAR ACTIVIDADES GENERADAS PARA UNA LECTURA
# =====================================================
@router.get(
    "/lecturas/{contenido_id}/actividades",
    response_model=list[ActividadResponse]
)
def listar_actividades_lectura(
    contenido_id: int,
    db: Session = Depends(get_db),
    usuario_actual: Usuario = Depends(obtener_usuario_actual)
):

    actividades = (
        db.query(Actividad)
        .filter(
            Actividad.contenido_id == contenido_id,
            Actividad.activo == True
        )
        .all()
    )

    return actividades


# =====================================================
# 3️⃣ OBTENER ACTIVIDAD ESPECÍFICA CON SUS PREGUNTAS
# =====================================================
@router.get(
    "/actividades/{actividad_id}",
    response_model=ActividadResponse
)
def obtener_actividad_ia(
    actividad_id: int,
    db: Session = Depends(get_db),
    usuario_actual: Usuario = Depends(obtener_usuario_actual)
):

    actividad = (
        db.query(Actividad)
        .filter(Actividad.id == actividad_id)
        .first()
    )

    if not actividad:
        raise HTTPException(status_code=404, detail="Actividad no encontrada")

    return actividad

# En app/routers/ia_actividades.py - AGREGAR estos endpoints:

# Actualizar actividad
@router.put("/actividades/{actividad_id}", response_model=ActividadResponse)
def actualizar_actividad(
    actividad_id: int,
    datos: ActividadBase,
    db: Session = Depends(get_db),
    usuario_actual: Usuario = Depends(obtener_usuario_actual)
):
    actividad = db.query(Actividad).filter(Actividad.id == actividad_id).first()
    
    if not actividad:
        raise HTTPException(status_code=404, detail="Actividad no encontrada")
    
    for key, value in datos.dict(exclude_unset=True).items():
        setattr(actividad, key, value)
    
    db.commit()
    db.refresh(actividad)
    
    return actividad


# Eliminar actividad
@router.delete("/actividades/{actividad_id}")
def eliminar_actividad(
    actividad_id: int,
    db: Session = Depends(get_db),
    usuario_actual: Usuario = Depends(obtener_usuario_actual)
):
    actividad = db.query(Actividad).filter(Actividad.id == actividad_id).first()
    
    if not actividad:
        raise HTTPException(status_code=404, detail="Actividad no encontrada")
    
    # Soft delete
    actividad.activo = False
    db.commit()
    
    return {"mensaje": "Actividad eliminada exitosamente"}


# Eliminar pregunta
@router.delete("/preguntas/{pregunta_id}")
def eliminar_pregunta(
    pregunta_id: int,
    db: Session = Depends(get_db),
    usuario_actual: Usuario = Depends(obtener_usuario_actual)
):
    from app.modelos import Pregunta
    
    pregunta = db.query(Pregunta).filter(Pregunta.id == pregunta_id).first()
    
    if not pregunta:
        raise HTTPException(status_code=404, detail="Pregunta no encontrada")
    
    db.delete(pregunta)
    db.commit()
    
    return {"mensaje": "Pregunta eliminada exitosamente"}
