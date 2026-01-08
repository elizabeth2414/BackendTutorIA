from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.config import get_db
from app.esquemas.contenido import (
    ContenidoLecturaCreate, ContenidoLecturaResponse, ContenidoLecturaUpdate,
    CategoriaLecturaCreate, CategoriaLecturaResponse, CategoriaLecturaUpdate,
    AudioReferenciaCreate, AudioReferenciaResponse
)
from app.servicios.contenido import (
    crear_contenido_lectura, obtener_contenidos, obtener_contenido,
    actualizar_contenido, eliminar_contenido,
    crear_categoria_lectura, obtener_categorias, obtener_categoria,
    actualizar_categoria, eliminar_categoria,
    crear_audio_referencia, obtener_audios_contenido
)
from app.servicios.seguridad import obtener_usuario_actual
from app.modelos import Usuario

router = APIRouter(prefix="/contenido", tags=["contenido"])

# Endpoints para Contenido de Lectura
@router.post("/lecturas", response_model=ContenidoLecturaResponse)
def crear_lectura(
    contenido: ContenidoLecturaCreate,
    db: Session = Depends(get_db),
    usuario_actual: Usuario = Depends(obtener_usuario_actual)
):
    """Crear nuevo contenido de lectura"""
    return crear_contenido_lectura(db, contenido)

@router.get("/lecturas", response_model=List[ContenidoLecturaResponse])
def listar_lecturas(
    skip: int = 0,
    limit: int = 100,
    curso_id: int = None,
    categoria_id: int = None,
    docente_id: int = None,
    activo: bool = True,
    db: Session = Depends(get_db)
):
    """Listar contenidos de lectura"""
    return obtener_contenidos(db, skip=skip, limit=limit, curso_id=curso_id, 
                            categoria_id=categoria_id, docente_id=docente_id, activo=activo)

@router.get("/lecturas/{contenido_id}", response_model=ContenidoLecturaResponse)
def obtener_lectura(
    contenido_id: int,
    db: Session = Depends(get_db)
):
    """Obtener contenido de lectura por ID"""
    db_contenido = obtener_contenido(db, contenido_id)
    if not db_contenido:
        raise HTTPException(status_code=404, detail="Contenido no encontrado")
    return db_contenido

@router.put("/lecturas/{contenido_id}", response_model=ContenidoLecturaResponse)
def actualizar_lectura(
    contenido_id: int,
    contenido: ContenidoLecturaUpdate,
    db: Session = Depends(get_db),
    usuario_actual: Usuario = Depends(obtener_usuario_actual)
):
    """Actualizar contenido de lectura"""
    return actualizar_contenido(db, contenido_id, contenido)

@router.delete("/lecturas/{contenido_id}")
def eliminar_lectura(
    contenido_id: int,
    db: Session = Depends(get_db),
    usuario_actual: Usuario = Depends(obtener_usuario_actual)
):
    """Eliminar contenido de lectura (soft delete)"""
    eliminar_contenido(db, contenido_id)
    return {"mensaje": "Contenido eliminado correctamente"}

# Endpoints para Categorías
@router.post("/categorias", response_model=CategoriaLecturaResponse)
def crear_categoria(
    categoria: CategoriaLecturaCreate,
    db: Session = Depends(get_db),
    usuario_actual: Usuario = Depends(obtener_usuario_actual)
):
    """Crear nueva categoría de lectura"""
    return crear_categoria_lectura(db, categoria)

@router.get("/categorias", response_model=List[CategoriaLecturaResponse])
def listar_categorias(
    skip: int = 0,
    limit: int = 100,
    activo: bool = True,
    db: Session = Depends(get_db)
):
    """Listar categorías de lectura"""
    return obtener_categorias(db, skip=skip, limit=limit, activo=activo)

@router.get("/categorias/{categoria_id}", response_model=CategoriaLecturaResponse)
def obtener_categoria_por_id(
    categoria_id: int,
    db: Session = Depends(get_db)
):
    """Obtener categoría por ID"""
    db_categoria = obtener_categoria(db, categoria_id)
    if not db_categoria:
        raise HTTPException(status_code=404, detail="Categoría no encontrada")
    return db_categoria

# Endpoints para Audios de Referencia
@router.post("/audios", response_model=AudioReferenciaResponse)
def crear_audio_referencia(
    audio: AudioReferenciaCreate,
    db: Session = Depends(get_db),
    usuario_actual: Usuario = Depends(obtener_usuario_actual)
):
    """Crear audio de referencia"""
    return crear_audio_referencia(db, audio)

@router.get("/lecturas/{contenido_id}/audios", response_model=List[AudioReferenciaResponse])
def listar_audios_contenido(
    contenido_id: int,
    db: Session = Depends(get_db)
):
    """Listar audios de referencia de un contenido"""
    return obtener_audios_contenido(db, contenido_id)