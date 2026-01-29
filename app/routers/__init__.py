from fastapi import APIRouter

from app.routers import (
    auth,
    docentes,
    estudiantes,
    cursos,
    contenido,
    evaluaciones,
    ejercicios,
    actividades,
    gamificacion,
    estadisticas,
    ia_routes,
    admin_docentes,
    categorias,
    lecturas,
    ia_actividades,
    usuarios, 
    padres,
    admin_dashboard,
    admin_estudiantes,
    actividades_estudiante,
    docentes_progreso,
)
from app.routers import (
    historial_pronunciacion,
    historial_practica_pronunciacion,
    historial_mejoras_ia,
    actividades_lectura,
)

api_router = APIRouter()


api_router.include_router(auth.router)
api_router.include_router(docentes.router)
api_router.include_router(estudiantes.router)
api_router.include_router(cursos.router)
api_router.include_router(contenido.router)
api_router.include_router(evaluaciones.router)
api_router.include_router(ejercicios.router)
api_router.include_router(actividades.router)
api_router.include_router(gamificacion.router)
api_router.include_router(estadisticas.router)
api_router.include_router(ia_routes.router)     
api_router.include_router(admin_docentes.router)
api_router.include_router(categorias.router)
api_router.include_router(lecturas.router)
api_router.include_router(ia_actividades.router)
api_router.include_router(padres.router)
api_router.include_router(admin_dashboard.router)
api_router.include_router(admin_estudiantes.router)
api_router.include_router(actividades_estudiante.router)
api_router.include_router(docentes_progreso.router)



api_router.include_router(usuarios.router)
api_router.include_router(historial_pronunciacion.router)
api_router.include_router(historial_practica_pronunciacion.router)
api_router.include_router(historial_mejoras_ia.router)
api_router.include_router(actividades_lectura.router)