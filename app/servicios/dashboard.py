from sqlalchemy.orm import Session
from app.modelos import Docente, Estudiante, ContenidoLectura, Actividad

def obtener_estadisticas_dashboard(db: Session):
    total_docentes = db.query(Docente).count()
    total_estudiantes = db.query(Estudiante).count()
    total_lecturas = db.query(ContenidoLectura).count()
    total_actividades = db.query(Actividad).count()

    return {
        "docentes": total_docentes,
        "estudiantes": total_estudiantes,
        "lecturas": total_lecturas,
        "actividades": total_actividades
    }
