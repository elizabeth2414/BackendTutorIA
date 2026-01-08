# app/esquemas/actividad_ia.py

from typing import List, Optional, Any
from pydantic import BaseModel


# ---------- PREGUNTAS ----------

class PreguntaBase(BaseModel):
    texto_pregunta: str
    tipo_respuesta: str
    opciones: Optional[Any] = None
    respuesta_correcta: Optional[str] = None
    puntuacion: int = 1
    explicacion: Optional[str] = None
    orden: int = 1


class PreguntaResponse(PreguntaBase):
    id: int

    model_config = {
        "from_attributes": True   # Pydantic v2
    }


# ---------- ACTIVIDAD ----------

class ActividadBase(BaseModel):
    tipo: str
    titulo: str
    descripcion: Optional[str] = None
    puntos_maximos: int
    tiempo_estimado: Optional[int] = None
    dificultad: Optional[int] = None
    configuracion: dict


class ActividadResponse(ActividadBase):
    id: int
    contenido_id: int
    preguntas: List[PreguntaResponse] = []

    model_config = {
        "from_attributes": True
    }


# ---------- REQUEST PARA GENERAR POR IA ----------

class GenerarActividadesIARequest(BaseModel):
    num_preguntas: int = 5
    incluir_verdadero_falso: bool = True
    incluir_multiple_choice: bool = True
    dificultad: int = 1
    idioma: str = "es"

    model_config = {
        "json_schema_extra": {
            "example": {
                "num_preguntas": 5,
                "incluir_verdadero_falso": True,
                "incluir_multiple_choice": True,
                "dificultad": 1,
                "idioma": "es"
            }
        }
    }


class GenerarActividadesIAResponse(BaseModel):
    contenido_id: int
    actividad_id: int
    total_preguntas: int
    mensaje: str
    actividad: ActividadResponse

    model_config = {
        "from_attributes": True
    }
