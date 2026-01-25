from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional

from app.config import get_db

# -----------------------------
# IMPORTS CORREGIDOS
# -----------------------------
from app.esquemas.curso import (
    CursoCreate,
    CursoResponse,
    CursoUpdate,
)

from app.esquemas.estudiante_curso import (
    EstudianteCursoCreate,
    EstudianteCursoResponse,
)

from app.servicios.curso import (
    crear_curso,
    obtener_cursos,
    obtener_cursos_activos,  # ← NUEVO
    obtener_curso,
    actualizar_curso as actualizar_curso_service,
    eliminar_curso as eliminar_curso_service,
    toggle_curso_activo,  # ← NUEVO
    inscribir_estudiante,
    obtener_estudiantes_curso,
    obtener_cursos_estudiante,
)

from app.servicios.seguridad import obtener_usuario_actual
from app.modelos import Usuario, Docente

router = APIRouter(prefix="/cursos", tags=["Cursos"])


# ================================================================
#   CREAR CURSO
# ================================================================
@router.post("/", response_model=CursoResponse)
def crear_nuevo_curso(
    curso: CursoCreate,
    db: Session = Depends(get_db),
    usuario_actual: Usuario = Depends(obtener_usuario_actual),
):
    """
    Crea un nuevo curso con código de acceso autogenerado.
    """
    # Buscar el docente asociado al usuario
    docente = (
        db.query(Docente)
        .filter(Docente.usuario_id == usuario_actual.id)
        .first()
    )

    # Si no existe docente, crearlo
    if not docente:
        docente = Docente(
            usuario_id=usuario_actual.id,
            activo=True,
        )
        db.add(docente)
        db.commit()
        db.refresh(docente)

    # Asignar docente_id automáticamente
    curso.docente_id = docente.id

    return crear_curso(db, curso)


# ================================================================
#   LISTAR CURSOS (Todos - activos e inactivos)
# ================================================================
@router.get("/", response_model=List[CursoResponse])
def listar_cursos(
    skip: int = 0,
    limit: int = 100,
    docente_id: Optional[int] = None,
    activo: Optional[bool] = None,
    db: Session = Depends(get_db),
    usuario_actual: Usuario = Depends(obtener_usuario_actual),
):
    """
    Lista todos los cursos (activos e inactivos).
    Para admin: lista de gestión.
    """
    # Si no se envía docente_id, usar el docente del usuario logueado
    if docente_id is None:
        docente = (
            db.query(Docente)
            .filter(Docente.usuario_id == usuario_actual.id)
            .first()
        )
        if not docente:
            return []
        docente_id = docente.id

    return obtener_cursos(
        db,
        skip=skip,
        limit=limit,
        docente_id=docente_id,
        activo=activo,
    )


# ================================================================
#   LISTAR SOLO CURSOS ACTIVOS (Para combobox)
# ================================================================
@router.get("/activos", response_model=List[CursoResponse])
def listar_cursos_activos(
    docente_id: Optional[int] = None,
    db: Session = Depends(get_db),
    usuario_actual: Usuario = Depends(obtener_usuario_actual),
):
    """
    Lista SOLO cursos activos.
    Úsala en combobox, selects, asignaciones, etc.
    """
    # Si no se envía docente_id, usar el docente del usuario logueado
    if docente_id is None:
        docente = (
            db.query(Docente)
            .filter(Docente.usuario_id == usuario_actual.id)
            .first()
        )
        if docente:
            docente_id = docente.id

    return obtener_cursos_activos(db, docente_id)


# ================================================================
#   OBTENER CURSO POR ID
# ================================================================
@router.get("/{curso_id}", response_model=CursoResponse)
def obtener_curso_por_id(
    curso_id: int,
    db: Session = Depends(get_db),
    usuario_actual: Usuario = Depends(obtener_usuario_actual),
):
    """Obtiene un curso específico por ID."""
    curso = obtener_curso(db, curso_id)
    if not curso:
        raise HTTPException(status_code=404, detail="Curso no encontrado")
    return curso


# ================================================================
#   ACTUALIZAR CURSO
# ================================================================
@router.put("/{curso_id}", response_model=CursoResponse)
def actualizar_curso_router(
    curso_id: int,
    datos: CursoUpdate,
    db: Session = Depends(get_db),
    usuario_actual: Usuario = Depends(obtener_usuario_actual),
):
    """Actualiza los datos de un curso."""
    return actualizar_curso_service(db, curso_id, datos)


# ================================================================
#   TOGGLE ACTIVO/INACTIVO
# ================================================================
@router.patch("/{curso_id}/toggle", response_model=CursoResponse)
def toggle_curso_router(
    curso_id: int,
    db: Session = Depends(get_db),
    usuario_actual: Usuario = Depends(obtener_usuario_actual),
):
    """
    Activa o desactiva un curso (toggle).
    Úsala para el botón de estado en el frontend.
    """
    return toggle_curso_activo(db, curso_id)


# ================================================================
#   ELIMINAR CURSO (Con validación de relaciones)
# ================================================================
@router.delete("/{curso_id}")
def eliminar_curso_router(
    curso_id: int,
    db: Session = Depends(get_db),
    usuario_actual: Usuario = Depends(obtener_usuario_actual),
):
    """
    Elimina un curso SOLO si no tiene relaciones.
    Si tiene estudiantes, lecturas o actividades, lanza error 400.
    """
    resultado = eliminar_curso_service(db, curso_id)
    return resultado


# ================================================================
#   INSCRIBIR ESTUDIANTE A UN CURSO
# ================================================================
@router.post("/{curso_id}/inscribir", response_model=EstudianteCursoResponse)
def inscribir_estudiante_curso(
    curso_id: int,
    inscripcion: EstudianteCursoCreate,
    db: Session = Depends(get_db),
    usuario_actual: Usuario = Depends(obtener_usuario_actual),
):
    """
    Inscribe un estudiante a un curso.
    Solo permite inscripción si el curso está activo.
    """
    return inscribir_estudiante(db, curso_id, inscripcion.estudiante_id)


# ================================================================
#   LISTAR ESTUDIANTES DE UN CURSO
# ================================================================
@router.get("/{curso_id}/estudiantes", response_model=List[EstudianteCursoResponse])
def listar_estudiantes_curso(
    curso_id: int,
    db: Session = Depends(get_db),
    usuario_actual: Usuario = Depends(obtener_usuario_actual),
):
    """Lista todos los estudiantes inscritos en un curso."""
    return obtener_estudiantes_curso(db, curso_id)


# ================================================================
#   LISTAR CURSOS DE UN ESTUDIANTE
# ================================================================
@router.get("/estudiante/{estudiante_id}", response_model=List[CursoResponse])
def listar_cursos_estudiante(
    estudiante_id: int,
    db: Session = Depends(get_db),
    usuario_actual: Usuario = Depends(obtener_usuario_actual),
):
    """
    Lista todos los cursos en los que está inscrito un estudiante.
    Solo retorna cursos activos.
    """
    return obtener_cursos_estudiante(db, estudiante_id)
