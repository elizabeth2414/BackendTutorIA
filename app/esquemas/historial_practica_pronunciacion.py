from typing import Optional
from datetime import datetime
from pydantic import BaseModel, ConfigDict


# =========================
# BASE
# =========================
class HistorialPracticaPronunciacionBase(BaseModel):
    estudiante_id: int
    ejercicio_id: int
    resultado_id: Optional[int] = None

    errores_detectados: Optional[int] = None
    errores_corregidos: Optional[int] = None

    puntuacion: Optional[float] = None
    tiempo_practica: Optional[int] = None

    retroalimentacion_ia: Optional[str] = None


# =========================
# CREATE
# =========================
class HistorialPracticaPronunciacionCreate(
    HistorialPracticaPronunciacionBase
):
    pass


# =========================
# RESPONSE
# =========================
class HistorialPracticaPronunciacionResponse(
    HistorialPracticaPronunciacionBase
):
    id: int
    fecha: datetime

    model_config = ConfigDict(from_attributes=True)
