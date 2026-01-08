from typing import Optional, Any
from datetime import datetime
from pydantic import BaseModel, ConfigDict


# =========================
# BASE
# =========================
class HistorialPronunciacionBase(BaseModel):
    estudiante_id: int
    contenido_id: int
    evaluacion_id: Optional[int] = None

    puntuacion_global: Optional[float] = None
    velocidad: Optional[float] = None
    fluidez: Optional[float] = None
    precision_palabras: Optional[float] = None
    palabras_por_minuto: Optional[float] = None

    errores: Optional[Any] = None
    retroalimentacion_ia: Optional[str] = None


# =========================
# CREATE
# =========================
class HistorialPronunciacionCreate(HistorialPronunciacionBase):
    pass


# =========================
# RESPONSE
# =========================
class HistorialPronunciacionResponse(HistorialPronunciacionBase):
    id: int
    fecha: datetime

    model_config = ConfigDict(from_attributes=True)
