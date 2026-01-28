from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime

from app.config import get_db
from app.servicios.seguridad import obtener_docente_actual
from app.modelos import (
    ContenidoLectura,
    Docente,
    # modelos relacionados (ajusta si están en otro archivo)
    EvaluacionLectura,
    HistorialPronunciacion,
    Actividad,
)

from pydantic import BaseModel

router = APIRouter(prefix="/lecturas", tags=["lecturas"])



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
    titulo: Optional[str] = None
    contenido: Optional[str] = None
    categoria_id: Optional[int] = None
    curso_id: Optional[int] = None
    nivel_dificultad: Optional[int] = None
    edad_recomendada: Optional[int] = None
    etiquetas: Optional[list] = None
    audio_url: Optional[str] = None


class LecturaResponse(LecturaBase):
    id: int
    docente_id: int

    class Config:
        from_attributes = True



def _lectura_tiene_datos_estudiante(db: Session, lectura_id: int) -> dict:
    """
    Revisa si esta lectura ya tiene actividad del estudiante.
    Si existe, NO se debe eliminar (ni físico ni "borrado lógico" sin aviso),
    solo se debe DESACTIVAR.
    """
    detalles = {
        "evaluaciones": 0,
        "historial_pronunciacion": 0,
        "actividades": 0,
    }


    if "EvaluacionLectura" in globals():
        detalles["evaluaciones"] = db.query(EvaluacionLectura).filter(
            EvaluacionLectura.contenido_id == lectura_id
        ).count()

    if "HistorialPronunciacion" in globals():
        detalles["historial_pronunciacion"] = db.query(HistorialPronunciacion).filter(
            HistorialPronunciacion.contenido_id == lectura_id
        ).count()

    if "Actividad" in globals():
        detalles["actividades"] = db.query(Actividad).filter(
            Actividad.contenido_id == lectura_id
        ).count()

    tiene = any(v > 0 for v in detalles.values())
    return {"tiene": tiene, "detalles": detalles}


def _get_lectura_docente(db: Session, lectura_id: int, docente_id: int) -> ContenidoLectura:
    lectura = (
        db.query(ContenidoLectura)
        .filter(ContenidoLectura.id == lectura_id)
        .filter(ContenidoLectura.docente_id == docente_id)
        .filter(ContenidoLectura.deleted_at.is_(None))  # si usas deleted_at
        .first()
    )
    if not lectura:
        raise HTTPException(status_code=404, detail="Lectura no encontrada")
    return lectura



@router.get("/", response_model=List[LecturaResponse])
def listar_lecturas(
    db: Session = Depends(get_db),
    docente: Docente = Depends(obtener_docente_actual)
):
    lecturas = (
        db.query(ContenidoLectura)
        .filter(ContenidoLectura.docente_id == docente.id)
        .filter(ContenidoLectura.activo == True)
        .filter(ContenidoLectura.deleted_at.is_(None))  # si usas deleted_at
        .order_by(ContenidoLectura.fecha_creacion.desc())
        .all()
    )
    return lecturas


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
        activo=True,
        deleted_at=None
    )

    db.add(lectura)
    db.commit()
    db.refresh(lectura)
    return lectura


@router.put("/{lectura_id}", response_model=LecturaResponse)
def actualizar_lectura(
    lectura_id: int,
    datos: LecturaUpdate,
    db: Session = Depends(get_db),
    docente: Docente = Depends(obtener_docente_actual)
):
    lectura = _get_lectura_docente(db, lectura_id, docente.id)

    for key, value in datos.dict(exclude_unset=True).items():
        setattr(lectura, key, value)

    db.commit()
    db.refresh(lectura)
    return lectura



@router.patch("/{lectura_id}/desactivar")
def desactivar_lectura(
    lectura_id: int,
    db: Session = Depends(get_db),
    docente: Docente = Depends(obtener_docente_actual)
):
    lectura = _get_lectura_docente(db, lectura_id, docente.id)

    lectura.activo = False
    lectura.deleted_at = datetime.utcnow()

    db.commit()
    return {"mensaje": "Lectura desactivada", "lectura_id": lectura_id}



@router.delete("/{lectura_id}")
def eliminar_lectura(
    lectura_id: int,
    db: Session = Depends(get_db),
    docente: Docente = Depends(obtener_docente_actual)
):
    lectura = _get_lectura_docente(db, lectura_id, docente.id)

    validacion = _lectura_tiene_datos_estudiante(db, lectura_id)

   
    if validacion["tiene"]:
        return HTTPException(
            status_code=400,
            detail={
                "mensaje": "No se puede eliminar la lectura porque ya tiene actividad de estudiantes (evaluaciones/historial/actividades).",
                "puede_desactivar": True,
                "detalles": validacion["detalles"],
            },
        )

    
    lectura.activo = False
    lectura.deleted_at = datetime.utcnow()
    db.commit()
    return {"mensaje": "Lectura desactivada (sin datos relacionados)", "lectura_id": lectura_id}

 
