from pydantic import BaseModel, EmailStr
from typing import Optional, List, Dict, Any
from datetime import datetime, date
from decimal import Decimal
from .historial_pronunciacion import (
    HistorialPronunciacionCreate,
    HistorialPronunciacionResponse,
)

from .historial_practica_pronunciacion import (
    HistorialPracticaPronunciacionCreate,
    HistorialPracticaPronunciacionResponse,
)

from .historial_mejoras_ia import (
    HistorialMejorasIACreate,
    HistorialMejorasIAResponse,
)

# Esquemas base comunes
class ModeloBase(BaseModel):
    class Config:
        from_attributes = True

class Mensaje(BaseModel):
    mensaje: str