from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.config import get_db
from app.servicios.seguridad import requiere_docente
from app.modelos import ContenidoLectura, CategoriaLectura, Curso, Docente, UsuarioRol

from pydantic import BaseModel
from typing import Optional

router = APIRouter(prefix="/categorias", tags=["categorias"])


# ============================================================
# ESQUEMAS Pydantic
# ============================================================

class CategoriaBase(BaseModel):
    nombre: str
    descripcion: Optional[str] = None
    edad_minima: int
    edad_maxima: int
    color: str = "#3498db"
    icono: Optional[str] = None


class CategoriaCreate(CategoriaBase):
    pass


class CategoriaUpdate(BaseModel):
    nombre: Optional[str]
    descripcion: Optional[str]
    edad_minima: Optional[int]
    edad_maxima: Optional[int]
    color: Optional[str]
    icono: Optional[str]
    activo: Optional[bool]


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
# 2. Crear categoría
# ============================================================

@router.post("/", response_model=CategoriaResponse)
def crear_categoria(
    datos: CategoriaCreate,
    db: Session = Depends(get_db),
    docente=Depends(requiere_docente)
):
    categoria = CategoriaLectura(
        nombre=datos.nombre,
        descripcion=datos.descripcion,
        edad_minima=datos.edad_minima,
        edad_maxima=datos.edad_maxima,
        color=datos.color,
        icono=datos.icono,
        activo=True
    )

    db.add(categoria)
    db.commit()
    db.refresh(categoria)

    return categoria


# ============================================================
# 3. Actualizar categoría
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

    # Actualizar valores
    for key, value in datos.dict(exclude_unset=True).items():
        setattr(categoria, key, value)

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

