from pydantic import BaseModel, EmailStr
from typing import Optional

class AdminCrearDocente(BaseModel):
    nombre: str
    apellido: str
    email: EmailStr
    password: str
    especialidad: Optional[str] = None
    institucion: Optional[str] = None
