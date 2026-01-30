from pydantic import BaseModel, Field, field_validator
from typing import Optional, List, Dict, Any
from datetime import datetime


from app.esquemas.curso import CursoResponse
from app.esquemas.docente import DocenteResponse


class CategoriaLecturaBase(BaseModel):
    nombre: str
    descripcion: Optional[str] = None
    edad_minima: int = Field(..., ge=5, le=12)
    edad_maxima: int = Field(..., ge=5, le=12)
    color: str = '#3498db'
    icono: Optional[str] = None
    activo: bool = True

    @field_validator("nombre")
    @classmethod
    def _validar_nombre_cat(cls, v: str):
        from app.validaciones.regex import validar_solo_letras
        return validar_solo_letras(v, min_len=3)

    @field_validator("descripcion")
    @classmethod
    def _validar_descripcion_cat(cls, v: str | None):
        if v is None:
            return v
        from app.validaciones.regex import validar_texto_libre
        return validar_texto_libre(v, max_len=500)

    @field_validator("color")
    @classmethod
    def _validar_color(cls, v: str):
        from app.validaciones.regex import validar_color_hex
        return validar_color_hex(v)

    @field_validator("icono")
    @classmethod
    def _validar_icono(cls, v: str | None):
        if v is None:
            return v
        v = v.strip()
        if len(v) > 4:
            raise ValueError("Icono demasiado largo")
        return v


class CategoriaLecturaCreate(CategoriaLecturaBase):
    pass


class CategoriaLecturaUpdate(BaseModel):
    nombre: Optional[str] = None
    descripcion: Optional[str] = None
    edad_minima: Optional[int] = None
    edad_maxima: Optional[int] = None
    color: Optional[str] = None
    icono: Optional[str] = None
    activo: Optional[bool] = None

    @field_validator("nombre")
    @classmethod
    def _validar_nombre_up(cls, v: str | None):
        if v is None:
            return v
        from app.validaciones.regex import validar_solo_letras
        return validar_solo_letras(v, min_len=3)

    @field_validator("descripcion")
    @classmethod
    def _validar_descripcion_up(cls, v: str | None):
        if v is None:
            return v
        from app.validaciones.regex import validar_texto_libre
        return validar_texto_libre(v, max_len=500)

    @field_validator("color")
    @classmethod
    def _validar_color_up(cls, v: str | None):
        if v is None:
            return v
        from app.validaciones.regex import validar_color_hex
        return validar_color_hex(v)

    @field_validator("icono")
    @classmethod
    def _validar_icono_up(cls, v: str | None):
        if v is None:
            return v
        v = v.strip()
        if len(v) > 4:
            raise ValueError("Icono demasiado largo")
        return v


class CategoriaLecturaResponse(CategoriaLecturaBase):
    id: int
    creado_en: datetime

    class Config:
        from_attributes = True


class ContenidoLecturaBase(BaseModel):
    titulo: str
    contenido: str
    audio_url: Optional[str] = None
    duracion_audio: Optional[int] = Field(default=None, ge=0)
    nivel_dificultad: int = Field(..., ge=1, le=5)
    edad_recomendada: int = Field(..., ge=5, le=12)
    palabras_clave: Optional[List[str]] = None
    etiquetas: Optional[Dict[str, Any]] = None
    por_defecto: bool = False
    publico: bool = False
    activo: bool = True

    @field_validator("titulo")
    @classmethod
    def _validar_titulo(cls, v: str):
        from app.validaciones.regex import validar_alfanum_espacio
        return validar_alfanum_espacio(v, min_len=3)

    @field_validator("contenido")
    @classmethod
    def _validar_contenido(cls, v: str):
        # Aquí permitimos texto más largo (lecturas), pero bloqueamos caracteres peligrosos.
        from app.validaciones.regex import validar_texto_libre
        return validar_texto_libre(v, max_len=10000)

    @field_validator("palabras_clave")
    @classmethod
    def _validar_palabras_clave(cls, v: Optional[List[str]]):
        if not v:
            return v
        from app.validaciones.regex import validar_alfanum_espacio
        return [validar_alfanum_espacio(x, min_len=2) for x in v]


class ContenidoLecturaCreate(ContenidoLecturaBase):
    curso_id: Optional[int] = None
    docente_id: Optional[int] = None
    categoria_id: Optional[int] = None


class ContenidoLecturaUpdate(BaseModel):
    titulo: Optional[str] = None
    contenido: Optional[str] = None
    audio_url: Optional[str] = None
    duracion_audio: Optional[int] = None
    nivel_dificultad: Optional[int] = None
    edad_recomendada: Optional[int] = None
    palabras_clave: Optional[List[str]] = None
    etiquetas: Optional[Dict[str, Any]] = None
    por_defecto: Optional[bool] = None
    publico: Optional[bool] = None
    activo: Optional[bool] = None

    @field_validator("titulo")
    @classmethod
    def _validar_titulo_up(cls, v: str | None):
        if v is None:
            return v
        from app.validaciones.regex import validar_alfanum_espacio
        return validar_alfanum_espacio(v, min_len=3)

    @field_validator("contenido")
    @classmethod
    def _validar_contenido_up(cls, v: str | None):
        if v is None:
            return v
        from app.validaciones.regex import validar_texto_libre
        return validar_texto_libre(v, max_len=10000)

    @field_validator("duracion_audio")
    @classmethod
    def _validar_duracion_up(cls, v: int | None):
        if v is None:
            return v
        if v < 0:
            raise ValueError("Duración inválida")
        return v

    @field_validator("nivel_dificultad")
    @classmethod
    def _validar_nivel_dificultad_up(cls, v: int | None):
        if v is None:
            return v
        if v < 1 or v > 5:
            raise ValueError("Nivel de dificultad inválido")
        return v

    @field_validator("edad_recomendada")
    @classmethod
    def _validar_edad_recomendada_up(cls, v: int | None):
        if v is None:
            return v
        if v < 5 or v > 12:
            raise ValueError("Edad recomendada inválida")
        return v

    @field_validator("palabras_clave")
    @classmethod
    def _validar_palabras_clave_up(cls, v: Optional[List[str]]):
        if not v:
            return v
        from app.validaciones.regex import validar_alfanum_espacio
        return [validar_alfanum_espacio(x, min_len=2) for x in v]


class ContenidoLecturaResponse(ContenidoLecturaBase):
    id: int
    curso_id: Optional[int]
    docente_id: Optional[int]
    categoria_id: Optional[int]
    fecha_creacion: datetime
    fecha_actualizacion: datetime

    # ✔ YA NO EN STRING
    curso: Optional[CursoResponse] = None
    docente: Optional[DocenteResponse] = None
    categoria: Optional[CategoriaLecturaResponse] = None

    class Config:
        from_attributes = True


class AudioReferenciaBase(BaseModel):
    audio_url: str
    duracion: int
    tipo: Optional[str] = None
    transcripcion: Optional[str] = None


class AudioReferenciaCreate(AudioReferenciaBase):
    contenido_id: int


class AudioReferenciaResponse(AudioReferenciaBase):
    id: int
    contenido_id: int
    fecha_creacion: datetime

    class Config:
        from_attributes = True
