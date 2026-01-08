from typing import Optional
from datetime import datetime
from pydantic import BaseModel, ConfigDict


# =========================
# BASE
# =========================
class HistorialMejorasIABase(BaseModel):
    estudiante_id: int
    palabra: Optional[str] = None
    tipo_error: Optional[str] = None

    precision_antes: Optional[float] = None
    precision_despues: Optional[float] = None


# =========================
# CREATE
# =========================
class HistorialMejorasIACreate(HistorialMejorasIABase):
    pass


# =========================
# RESPONSE
# =========================
class HistorialMejorasIAResponse(HistorialMejorasIABase):
    id: int
    fecha: datetime

    model_config = ConfigDict(from_attributes=True)
