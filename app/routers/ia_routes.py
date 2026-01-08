# app/routers/ia_routes.py

import os
import uuid
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.config import get_db
from app.logs.logger import logger
from app.modelos import (
    ContenidoLectura,
    Estudiante,
    Padre,
)
from app.servicios.seguridad import obtener_usuario_actual
from app.modelos import Usuario
from app.servicios.ia_lectura_service import ServicioAnalisisLectura
from app.servicios.manager_aprendizaje_ia import ManagerAprendizajeIA

router = APIRouter(prefix="/ia", tags=["IA Lectura"])

# Directorios para guardar audios
UPLOAD_AUDIO_DIR = "uploads/audio"
TTS_DIR = "uploads/tts"
PRACTICA_AUDIO_DIR = "uploads/practica"

analizador = ServicioAnalisisLectura(modelo="small")
manager_ia = ManagerAprendizajeIA()  # ✅ Ya lo tienes instanciado


def _asegurar_directorios() -> None:
    os.makedirs(UPLOAD_AUDIO_DIR, exist_ok=True)
    os.makedirs(TTS_DIR, exist_ok=True)
    os.makedirs(PRACTICA_AUDIO_DIR, exist_ok=True)


def _obtener_padre_actual(db: Session, usuario_actual: Usuario) -> Padre:
    padre = (
        db.query(Padre)
        .filter(Padre.usuario_id == usuario_actual.id)
        .first()
    )
    if not padre:
        raise HTTPException(
            status_code=403,
            detail="El usuario actual no es un padre registrado.",
        )
    return padre


def _verificar_estudiante_de_padre(
    db: Session,
    padre: Padre,
    estudiante_id: int,
) -> Estudiante:
    estudiante = (
        db.query(Estudiante)
        .filter(
            Estudiante.id == estudiante_id,
            Estudiante.padre_id == padre.id,
        )
        .first()
    )
    if not estudiante:
        raise HTTPException(
            status_code=403,
            detail="No tienes permiso para acceder a este estudiante.",
        )
    return estudiante


# ============================================================
# 1. Obtener texto de la lectura
# ============================================================
@router.get("/lectura-texto/{contenido_id}")
def obtener_texto_lectura(
    contenido_id: int,
    db: Session = Depends(get_db),
    usuario_actual: Usuario = Depends(obtener_usuario_actual),
):
    contenido = (
        db.query(ContenidoLectura)
        .filter(ContenidoLectura.id == contenido_id)
        .first()
    )
    if not contenido:
        raise HTTPException(status_code=404, detail="Contenido de lectura no encontrado.")

    return {
        "id": contenido.id,
        "titulo": contenido.titulo,
        "contenido": contenido.contenido,
    }


# ============================================================
# 2. Obtener audio de la lectura
# ============================================================
@router.get("/lectura-audio/{contenido_id}")
def obtener_audio_lectura(
    contenido_id: int,
    db: Session = Depends(get_db),
    usuario_actual: Usuario = Depends(obtener_usuario_actual),
):
    contenido = (
        db.query(ContenidoLectura)
        .filter(ContenidoLectura.id == contenido_id)
        .first()
    )
    if not contenido:
        raise HTTPException(status_code=404, detail="Contenido de lectura no encontrado.")

    if contenido.audio_url and os.path.exists(contenido.audio_url):
        return FileResponse(contenido.audio_url, media_type="audio/mpeg")

    raise HTTPException(status_code=404, detail="No hay audio disponible para esta lectura.")


# ============================================================
# 3. ✅ ANALIZAR LECTURA COMPLETA CON EJERCICIOS
# ============================================================
@router.post("/analizar-lectura")
async def analizar_lectura_endpoint(
    estudiante_id: int = Form(...),
    contenido_id: int = Form(...),
    audio: UploadFile = File(...),
    evaluacion_id: Optional[int] = Form(None),
    db: Session = Depends(get_db),
    usuario_actual: Usuario = Depends(obtener_usuario_actual),
):
    """
    ✅ CAMBIO CLAVE: Ahora usa manager_ia.procesar_lectura()
    que incluye tanto el análisis como la generación de ejercicios.
    """
    _asegurar_directorios()

    padre = _obtener_padre_actual(db, usuario_actual)
    _verificar_estudiante_de_padre(db, padre, estudiante_id)

    ext = os.path.splitext(audio.filename or "")[1] or ".wav"
    filename = f"lectura_{estudiante_id}_{contenido_id}_{uuid.uuid4().hex}{ext}"
    audio_path = os.path.join(UPLOAD_AUDIO_DIR, filename)

    try:
        with open(audio_path, "wb") as f:
            contenido_bytes = await audio.read()
            f.write(contenido_bytes)

        # ✅ CAMBIO: Usar manager_ia en lugar de analizador directamente
        resultado = manager_ia.procesar_lectura(
            db=db,
            estudiante_id=estudiante_id,
            contenido_id=contenido_id,
            audio_path=audio_path,
            evaluacion_id=evaluacion_id,
        )

        logger.info(f"✅ Análisis completo | Ejercicios generados: {len(resultado.get('ejercicios_recomendados', []))}")

        return resultado

    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Error al analizar lectura con IA")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================
# 4. Práctica de ejercicio
# ============================================================
@router.post("/practicar-ejercicio")
async def practicar_ejercicio_endpoint(
    estudiante_id: int = Form(...),
    ejercicio_id: int = Form(...),
    audio: UploadFile = File(...),
    db: Session = Depends(get_db),
    usuario_actual: Usuario = Depends(obtener_usuario_actual),
):
    logger.info(f"📥 Recibida petición de práctica | estudiante={estudiante_id} | ejercicio={ejercicio_id}")
    
    _asegurar_directorios()

    try:
        padre = _obtener_padre_actual(db, usuario_actual)
        _verificar_estudiante_de_padre(db, padre, estudiante_id)

        ext = os.path.splitext(audio.filename or "")[1] or ".wav"
        filename = f"practica_{ejercicio_id}_{uuid.uuid4().hex}{ext}"
        audio_path = os.path.join(PRACTICA_AUDIO_DIR, filename)

        logger.info(f"💾 Guardando audio | path={audio_path}")
        
        with open(audio_path, "wb") as f:
            contenido_bytes = await audio.read()
            f.write(contenido_bytes)

        logger.info(f"✅ Audio guardado | size={len(contenido_bytes)} bytes")

        resultado = manager_ia.practicar_ejercicio(
            db=db,
            estudiante_id=estudiante_id,
            ejercicio_id=ejercicio_id,
            audio_path=audio_path,
        )

        logger.info("🎉 Práctica completada exitosamente")
        return resultado

    except HTTPException:
        raise
    except ValueError as ve:
        logger.error(f"❌ Error de validación: {ve}")
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        logger.exception("❌ Error al analizar práctica de ejercicio con IA")
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")