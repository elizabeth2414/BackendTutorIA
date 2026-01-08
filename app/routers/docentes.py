from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy.sql import func
from typing import List

from app.config import get_db

# MODELOS
from app.modelos import (
    Usuario, Docente, Curso, Estudiante, Actividad, EstudianteCurso
)

# SEGURIDAD
from app.servicios.seguridad import obtener_usuario_actual

# ESQUEMAS
from app.esquemas.docente import DocenteCreate, DocenteResponse, DocenteUpdate
from app.esquemas.estudiante import EstudianteCreateDocente, EstudianteUpdateDocente


router = APIRouter(prefix="/docentes", tags=["docentes"])


# ================================================================
#  FUNCIÓN QUE GARANTIZA QUE EL DOCENTE EXISTA
# ================================================================
def obtener_o_crear_docente(db: Session, usuario_id: int):
    docente = db.query(Docente).filter(Docente.usuario_id == usuario_id).first()

    if not docente:
        docente = Docente(usuario_id=usuario_id, activo=True)
        db.add(docente)
        db.commit()
        db.refresh(docente)

    return docente


# ================================================================
#   LISTAR DOCENTES (ADMIN)
# ================================================================
@router.get("/", response_model=List[DocenteResponse])
def listar_docentes(
    skip: int = 0,
    limit: int = 100,
    activo: bool = True,
    db: Session = Depends(get_db),
    usuario_actual: Usuario = Depends(obtener_usuario_actual)
):
    docentes = (
        db.query(Docente)
        .filter(Docente.activo == activo)
        .offset(skip)
        .limit(limit)
        .all()
    )
    return docentes


# ================================================================
#   DASHBOARD RESUMEN
# ================================================================
@router.get("/dashboard/resumen")
def dashboard_resumen(
    db: Session = Depends(get_db),
    usuario_actual: Usuario = Depends(obtener_usuario_actual)
):
    docente = obtener_o_crear_docente(db, usuario_actual.id)

    estudiantes = db.query(Estudiante).filter(Estudiante.docente_id == docente.id)

    total_estudiantes = estudiantes.count()
    activos = estudiantes.filter(Estudiante.activo == True).count()
    inactivos = total_estudiantes - activos

    total_actividades = db.query(Actividad).count()

    niveles = (
        db.query(Estudiante.nivel_educativo, func.count(Estudiante.id))
        .filter(Estudiante.docente_id == docente.id)
        .group_by(Estudiante.nivel_educativo)
        .all()
    )

    return {
        "total_estudiantes": total_estudiantes,
        "estudiantes_activos": activos,
        "estudiantes_inactivos": inactivos,
        "total_actividades": total_actividades,
        "niveles": {f"nivel_{n}": c for n, c in niveles}
    }


# ================================================================
#   DASHBOARD - DATOS ESTÁTICOS
# ================================================================
@router.get("/dashboard/progreso-mensual")
def progreso_mensual():
    return [
        {"mes": "Enero", "valor": 45},
        {"mes": "Febrero", "valor": 60},
        {"mes": "Marzo", "valor": 72},
        {"mes": "Abril", "valor": 80},
        {"mes": "Mayo", "valor": 65},
    ]


@router.get("/dashboard/rendimiento-cursos")
def rendimiento_cursos():
    return [
        {"curso": "Lectura Inicial", "promedio": 8.4},
        {"curso": "Comprensión 1", "promedio": 7.8},
        {"curso": "Comprensión 2", "promedio": 9.2},
    ]


@router.get("/dashboard/niveles")
def niveles_estudiantes(
    db: Session = Depends(get_db),
    usuario_actual: Usuario = Depends(obtener_usuario_actual)
):
    docente = obtener_o_crear_docente(db, usuario_actual.id)

    niveles = (
        db.query(Estudiante.nivel_educativo, func.count(Estudiante.id))
        .filter(Estudiante.docente_id == docente.id)
        .group_by(Estudiante.nivel_educativo)
        .all()
    )

    return {f"nivel_{n}": c for n, c in niveles}


# ================================================================
#   CURSOS DEL DOCENTE (FUNCIONAL)
# ================================================================
@router.get("/cursos")
def cursos_docente(
    db: Session = Depends(get_db),
    usuario_actual: Usuario = Depends(obtener_usuario_actual)
):
    docente = obtener_o_crear_docente(db, usuario_actual.id)

    cursos = (
        db.query(Curso)
        .filter(Curso.docente_id == docente.id)
        .all()
    )

    return [
        {
            "id": c.id,
            "nombre": c.nombre,
            "nivel": c.nivel,
            "activo": c.activo
        }
        for c in cursos
    ]


# ================================================================
#   CREAR ESTUDIANTE
# ================================================================
@router.post("/estudiantes")
def crear_estudiante_docente(
    datos: EstudianteCreateDocente,
    db: Session = Depends(get_db),
    usuario_actual: Usuario = Depends(obtener_usuario_actual)
):
    docente = obtener_o_crear_docente(db, usuario_actual.id)

    est = Estudiante(
        usuario_id=None,
        docente_id=docente.id,
        nombre=datos.nombre,
        apellido=datos.apellido,
        fecha_nacimiento=datos.fecha_nacimiento,
        nivel_educativo=datos.nivel_educativo,
        necesidades_especiales=datos.necesidades_especiales
    )

    db.add(est)
    db.commit()
    db.refresh(est)

    estcurso = EstudianteCurso(
        estudiante_id=est.id,
        curso_id=datos.curso_id
    )
    db.add(estcurso)
    db.commit()

    return {"id": est.id, "curso_id": datos.curso_id}


# ================================================================
#   LISTAR ESTUDIANTES DEL DOCENTE (FUNCIONAL)
# ================================================================
@router.get("/estudiantes")
def listar_estudiantes_docente(
    db: Session = Depends(get_db),
    usuario_actual: Usuario = Depends(obtener_usuario_actual)
):
    docente = obtener_o_crear_docente(db, usuario_actual.id)

    ests = (
        db.query(
            Estudiante.id,
            Estudiante.nombre,
            Estudiante.apellido,
            Estudiante.nivel_educativo,
            Curso.nombre.label("curso_nombre")
        )
        .join(EstudianteCurso, EstudianteCurso.estudiante_id == Estudiante.id)
        .join(Curso, Curso.id == EstudianteCurso.curso_id)
        .filter(Estudiante.docente_id == docente.id)
        .all()
    )

    return [row._asdict() for row in ests]

@router.get("/estudiantes/{estudiante_id}")
def obtener_estudiante_docente(
    estudiante_id: int,
    db: Session = Depends(get_db),
    usuario_actual: Usuario = Depends(obtener_usuario_actual)
):
    docente = obtener_o_crear_docente(db, usuario_actual.id)

    est = (
        db.query(Estudiante)
        .join(EstudianteCurso, EstudianteCurso.estudiante_id == Estudiante.id)
        .filter(Estudiante.id == estudiante_id)
        .filter(Estudiante.docente_id == docente.id)
        .first()
    )

    if not est:
        raise HTTPException(404, "Estudiante no encontrado")

    curso_asignado = (
        db.query(EstudianteCurso.curso_id)
        .filter(EstudianteCurso.estudiante_id == estudiante_id)
        .first()
    )

    return {
        "id": est.id,
        "nombre": est.nombre,
        "apellido": est.apellido,
        "fecha_nacimiento": est.fecha_nacimiento,
        "nivel_educativo": est.nivel_educativo,
        "necesidades_especiales": est.necesidades_especiales,
        "curso_id": curso_asignado[0] if curso_asignado else None
    }

# ================================================================
#   ELIMINAR ESTUDIANTE (DOCENTE)
# ================================================================
@router.delete("/estudiantes/{estudiante_id}")
def eliminar_estudiante_docente(
    estudiante_id: int,
    db: Session = Depends(get_db),
    usuario_actual: Usuario = Depends(obtener_usuario_actual)
):

    # 1. Obtener docente (si no existe se crea)
    docente = obtener_o_crear_docente(db, usuario_actual.id)

    # 2. Buscar estudiante que pertenezca a este docente
    estudiante = (
        db.query(Estudiante)
        .filter(Estudiante.id == estudiante_id)
        .filter(Estudiante.docente_id == docente.id)
        .first()
    )

    if not estudiante:
        raise HTTPException(
            status_code=404,
            detail="Estudiante no encontrado o no pertenece a este docente."
        )

    # 3. Eliminar relaciones en EstudianteCurso
    db.query(EstudianteCurso).filter(EstudianteCurso.estudiante_id == estudiante_id).delete()

    # 4. Eliminar estudiante
    db.delete(estudiante)
    db.commit()

    return {
        "mensaje": "Estudiante eliminado correctamente",
        "id": estudiante_id
    }


# ================================================================
#   CRUD DOCENTES DINÁMICOS (AL FINAL)
# ================================================================
@router.post("/", response_model=DocenteResponse)
def crear_nuevo_docente(
    docente: DocenteCreate,
    db: Session = Depends(get_db),
    usuario_actual: Usuario = Depends(obtener_usuario_actual)
):
    nuevo = Docente(usuario_id=docente.usuario_id, activo=True)
    db.add(nuevo)
    db.commit()
    db.refresh(nuevo)
    return nuevo


@router.get("/{docente_id}", response_model=DocenteResponse)
def obtener_docente_por_id(
    docente_id: int,
    db: Session = Depends(get_db),
    usuario_actual: Usuario = Depends(obtener_usuario_actual)
):
    docente = db.query(Docente).filter(Docente.id == docente_id).first()
    if not docente:
        raise HTTPException(404, "Docente no encontrado")
    return docente


@router.put("/{docente_id}", response_model=DocenteResponse)
def actualizar_docente_endpoint(
    docente_id: int,
    datos: DocenteUpdate,
    db: Session = Depends(get_db),
    usuario_actual: Usuario = Depends(obtener_usuario_actual)
):
    docente = db.query(Docente).filter(Docente.id == docente_id).first()
    if not docente:
        raise HTTPException(404, "Docente no encontrado")

    for campo, valor in datos.dict(exclude_unset=True).items():
        setattr(docente, campo, valor)

    db.commit()
    db.refresh(docente)
    return docente


@router.delete("/{docente_id}")
def eliminar_docente_endpoint(
    docente_id: int,
    db: Session = Depends(get_db),
    usuario_actual: Usuario = Depends(obtener_usuario_actual)
):
    docente = db.query(Docente).filter(Docente.id == docente_id).first()
    if not docente:
        raise HTTPException(404, "Docente no encontrado")

    db.delete(docente)
    db.commit()

    return {"mensaje": "Docente eliminado correctamente"}
