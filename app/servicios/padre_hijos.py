# app/servicios/padre_hijos.py
from typing import List
from sqlalchemy.orm import Session

from app.modelos import Padre, Estudiante, EstudianteCurso
from app.esquemas.estudiante import EstudianteResponse
from app.esquemas.curso import CursoResponse
from app.esquemas.padre_hijos import EstudianteConCursosResponse


def obtener_hijos_con_cursos(
    db: Session,
    usuario_id: int,
) -> List[EstudianteConCursosResponse]:
    # Buscar padre
    padre = (
        db.query(Padre)
        .filter(Padre.usuario_id == usuario_id)
        .first()
    )

    if not padre:
        return []

    # Buscar hijos del padre
    hijos = (
        db.query(Estudiante)
        .filter(Estudiante.padre_id == padre.id)
        .all()
    )

    resultado: List[EstudianteConCursosResponse] = []

    for hijo in hijos:
        # Buscar cursos asociados al hijo
        relaciones = (
            db.query(EstudianteCurso)
            .filter(EstudianteCurso.estudiante_id == hijo.id)
            .all()
        )

        cursos = [
            CursoResponse.model_validate(rel.curso)
            for rel in relaciones
            if rel.curso
        ]

        resultado.append(
            EstudianteConCursosResponse(
                estudiante=EstudianteResponse.model_validate(hijo),
                cursos=cursos,
            )
        )

    return resultado
