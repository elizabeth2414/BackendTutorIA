from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from typing import List

from app.config import get_db
from app.servicios.seguridad import obtener_docente_actual
from app.modelos import ContenidoLectura, CategoriaLectura, Curso, Docente
from pydantic import BaseModel
from typing import Optional

router = APIRouter(prefix="/lecturas", tags=["lecturas"])


# ============================================================
#    ESQUEMAS Pydantic
# ============================================================

class LecturaBase(BaseModel):
    titulo: str
    contenido: str
    categoria_id: int
    curso_id: int
    nivel_dificultad: int
    edad_recomendada: int
    etiquetas: Optional[list] = []
    audio_url: Optional[str] = None


class LecturaCreate(LecturaBase):
    pass


class LecturaUpdate(BaseModel):
    titulo: Optional[str]
    contenido: Optional[str]
    categoria_id: Optional[int]
    curso_id: Optional[int]
    nivel_dificultad: Optional[int]
    edad_recomendada: Optional[int]
    etiquetas: Optional[list]
    audio_url: Optional[str]


class LecturaResponse(LecturaBase):
    id: int
    docente_id: int

    class Config:
        from_attributes = True


# ============================================================
#    🔵 1. LISTAR LECTURAS DEL DOCENTE
# ============================================================

@router.get("/", response_model=List[LecturaResponse])
def listar_lecturas(
    db: Session = Depends(get_db),
    docente: Docente = Depends(obtener_docente_actual)  
):
    lecturas = (
        db.query(ContenidoLectura)
        .filter(ContenidoLectura.docente_id == docente.id)
        .filter(ContenidoLectura.activo == True)
        .order_by(ContenidoLectura.fecha_creacion.desc())
        .all()
    )
    return lecturas


# ============================================================
#    🟢 2. CREAR LECTURA
# ============================================================

@router.post("/", response_model=LecturaResponse)
def crear_lectura(
    datos: LecturaCreate,
    db: Session = Depends(get_db),
    docente: Docente = Depends(obtener_docente_actual)  
):
    lectura = ContenidoLectura(
        titulo=datos.titulo,
        contenido=datos.contenido,
        categoria_id=datos.categoria_id,
        curso_id=datos.curso_id,
        docente_id=docente.id,  
        nivel_dificultad=datos.nivel_dificultad,
        edad_recomendada=datos.edad_recomendada,
        etiquetas=datos.etiquetas,
        audio_url=datos.audio_url,
    )

    db.add(lectura)
    db.commit()
    db.refresh(lectura)

    return lectura


# ============================================================
#    🟡 3. ACTUALIZAR LECTURA
# ============================================================

@router.put("/{lectura_id}", response_model=LecturaResponse)
def actualizar_lectura(
    lectura_id: int,
    datos: LecturaUpdate,
    db: Session = Depends(get_db),
    docente: Docente = Depends(obtener_docente_actual)  
):
    lectura = (
        db.query(ContenidoLectura)
        .filter(ContenidoLectura.id == lectura_id)
        .filter(ContenidoLectura.docente_id == docente.id)
        .first()
    )

    if not lectura:
        raise HTTPException(404, "Lectura no encontrada")

    for key, value in datos.dict(exclude_unset=True).items():
        setattr(lectura, key, value)

    db.commit()
    db.refresh(lectura)

    return lectura


# ============================================================
#    🔴 4. ELIMINAR LECTURA (DESACTIVAR)
# ============================================================

@router.delete("/{lectura_id}")
def eliminar_lectura(
    lectura_id: int,
    db: Session = Depends(get_db),
    docente: Docente = Depends(obtener_docente_actual)  # ✅ CORREGIDO
):
    lectura = (
        db.query(ContenidoLectura)
        .filter(ContenidoLectura.id == lectura_id)
        .filter(ContenidoLectura.docente_id == docente.id)
        .first()
    )

    if not lectura:
        raise HTTPException(404, "Lectura no encontrada")

    lectura.activo = False
    db.commit()

    return {"mensaje": "Lectura eliminada"}
