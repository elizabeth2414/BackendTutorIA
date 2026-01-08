from datetime import date, datetime
from typing import Optional, Any
from pydantic import BaseModel, field_validator

from app.esquemas.usuario import UsuarioResponse
from app.esquemas.estudiante import EstudianteResponse



class PadreBase(BaseModel):
    telefono_contacto: Optional[str] = None
    parentesco: Optional[str] = None
    notificaciones_activas: bool = True
    activo: bool = True


class PadreCreate(PadreBase):
    usuario_id: Optional[int] = None


class PadreUpdate(BaseModel):
    telefono_contacto: Optional[str] = None
    parentesco: Optional[str] = None
    notificaciones_activas: Optional[bool] = None
    activo: Optional[bool] = None


class PadreResponse(PadreBase):
    id: int
    usuario_id: Optional[int]
    creado_en: datetime
    usuario: Optional["UsuarioResponse"] = None

    model_config = {"from_attributes": True}


class AccesoPadreBase(BaseModel):
    email_padre: Optional[str] = None
    rol_padre: str = "padre"
    puede_ver_progreso: bool = True


class AccesoPadreCreate(AccesoPadreBase):
    estudiante_id: int
    padre_id: Optional[int] = None


class AccesoPadreResponse(AccesoPadreBase):
    id: int
    estudiante_id: int
    padre_id: Optional[int]
    creado_en: datetime
    estudiante: Optional["EstudianteResponse"] = None
    padre: Optional["PadreResponse"] = None

    model_config = {"from_attributes": True}


class VincularHijoRequest(BaseModel):
    nombre: str
    apellido: str
    fecha_nacimiento: date | str

    @field_validator("nombre", "apellido")
    def limpiar_cadenas(cls, v):
        return v.strip().title()

    @field_validator("fecha_nacimiento", mode="before")
    def normalizar_fecha(cls, v):
        """
        Acepta múltiples formatos de fecha
        """
        if isinstance(v, date):
            return v

        formatos = [
            "%Y-%m-%d",
            "%Y/%m/%d",
            "%Y-%m-%dT%H:%M:%S",
            "%d-%m-%Y",
        ]

        for f in formatos:
            try:
                return datetime.strptime(str(v), f).date()
            except Exception:
                pass

        raise ValueError("Formato de fecha inválido. Use YYYY-MM-DD")


class LecturaConActividades(BaseModel):
    id: int
    titulo: str
    descripcion: Optional[str]
    contenido: str
    actividades: list[Any] = []

    model_config = {"from_attributes": True}
