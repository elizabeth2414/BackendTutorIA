from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.config import get_db
from app.servicios.seguridad import requiere_docente
from app.modelos import ContenidoLectura, CategoriaLectura, Curso, Docente, UsuarioRol

from pydantic import BaseModel, validator
from typing import Optional

router = APIRouter(prefix="/categorias", tags=["categorias"])


# ============================================================
# ESQUEMAS Pydantic (VALIDACIÓN: 7-10 AÑOS)
# ============================================================

class CategoriaBase(BaseModel):
    nombre: str
    descripcion: Optional[str] = None
    edad_minima: int
    edad_maxima: int
    color: str = "#3498db"
    icono: Optional[str] = None

    @validator('edad_minima')
    def validar_edad_minima(cls, v):
        if v < 7 or v > 10:
            raise ValueError('La edad mínima debe estar entre 7 y 10 años')
        return v

    @validator('edad_maxima')
    def validar_edad_maxima(cls, v):
        if v < 7 or v > 10:
            raise ValueError('La edad máxima debe estar entre 7 y 10 años')
        return v


class CategoriaCreate(CategoriaBase):
    pass


class CategoriaUpdate(BaseModel):
    nombre: Optional[str] = None
    descripcion: Optional[str] = None
    edad_minima: Optional[int] = None
    edad_maxima: Optional[int] = None
    color: Optional[str] = None
    icono: Optional[str] = None
    activo: Optional[bool] = None

    @validator('edad_minima')
    def validar_edad_minima(cls, v):
        if v is not None and (v < 7 or v > 10):
            raise ValueError('La edad mínima debe estar entre 7 y 10 años')
        return v

    @validator('edad_maxima')
    def validar_edad_maxima(cls, v):
        if v is not None and (v < 7 or v > 10):
            raise ValueError('La edad máxima debe estar entre 7 y 10 años')
        return v


class CategoriaResponse(CategoriaBase):
    id: int
    activo: bool

    class Config:
        from_attributes = True


# ============================================================
# 1. Obtener todas las categorías del docente
# ============================================================

@router.get("/", response_model=list[CategoriaResponse])
def listar_categorias(
    db: Session = Depends(get_db),
    docente=Depends(requiere_docente)
):
    categorias = (
        db.query(CategoriaLectura)
        .filter(CategoriaLectura.activo == True)
        .order_by(CategoriaLectura.nombre.asc())
        .all()
    )
    return categorias


# ============================================================
# 2. Crear categoría (VALIDACIÓN: 7-10 AÑOS)
# ============================================================

@router.post("/", response_model=CategoriaResponse)
def crear_categoria(
    datos: CategoriaCreate,
    db: Session = Depends(get_db),
    docente=Depends(requiere_docente)
):
    # Validar que edad_minima <= edad_maxima
    if datos.edad_minima > datos.edad_maxima:
        raise HTTPException(
            status_code=422,
            detail="La edad mínima no puede ser mayor que la edad máxima"
        )

    categoria = CategoriaLectura(
        nombre=datos.nombre,
        descripcion=datos.descripcion or "",
        edad_minima=datos.edad_minima,
        edad_maxima=datos.edad_maxima,
        color=datos.color,
        icono=datos.icono or "",
        activo=True
    )

    db.add(categoria)
    db.commit()
    db.refresh(categoria)

    return categoria


# ============================================================
# 3. Actualizar categoría (VALIDACIÓN: 7-10 AÑOS)
# ============================================================

@router.put("/{categoria_id}", response_model=CategoriaResponse)
def actualizar_categoria(
    categoria_id: int,
    datos: CategoriaUpdate,
    db: Session = Depends(get_db),
    docente=Depends(requiere_docente)
):
    categoria = db.query(CategoriaLectura).filter(CategoriaLectura.id == categoria_id).first()

    if not categoria:
        raise HTTPException(status_code=404, detail="Categoría no encontrada")

    # Obtener valores actuales o nuevos
    nueva_edad_minima = datos.edad_minima if datos.edad_minima is not None else categoria.edad_minima
    nueva_edad_maxima = datos.edad_maxima if datos.edad_maxima is not None else categoria.edad_maxima

    # Validar que edad_minima <= edad_maxima
    if nueva_edad_minima > nueva_edad_maxima:
        raise HTTPException(
            status_code=422,
            detail="La edad mínima no puede ser mayor que la edad máxima"
        )

    # Actualizar valores solo si vienen en el request
    if datos.nombre is not None:
        categoria.nombre = datos.nombre
    if datos.descripcion is not None:
        categoria.descripcion = datos.descripcion
    if datos.edad_minima is not None:
        categoria.edad_minima = datos.edad_minima
    if datos.edad_maxima is not None:
        categoria.edad_maxima = datos.edad_maxima
    if datos.color is not None:
        categoria.color = datos.color
    if datos.icono is not None:
        categoria.icono = datos.icono
    if datos.activo is not None:
        categoria.activo = datos.activo

    db.commit()
    db.refresh(categoria)

    return categoria


# ============================================================
# 4. Eliminar categoría (desactivar)
# ============================================================

@router.delete("/{categoria_id}")
def eliminar_categoria(
    categoria_id: int,
    db: Session = Depends(get_db),
    docente=Depends(requiere_docente)
):
    categoria = db.query(CategoriaLectura).filter(CategoriaLectura.id == categoria_id).first()

    if not categoria:
        raise HTTPException(status_code=404, detail="Categoría no encontrada")

    categoria.activo = False
    db.commit()

    return {"mensaje": "Categoría eliminada correctamente"}

