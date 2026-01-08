from pydantic import BaseModel

class DashboardStats(BaseModel):
    docentes: int
    estudiantes: int
    lecturas: int
    actividades: int
