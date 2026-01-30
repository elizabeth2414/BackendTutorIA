"""Regex y helpers para validar entradas de texto.

Reglas (según tu requerimiento):
- Campos solo letras: permite letras Unicode (incluye tildes/ñ) y espacios.
- Campos solo números: dígitos 0-9.
- Campos alfanuméricos: letras/números/espacios (sin símbolos).

Para campos de *texto libre* (descripciones/lecturas), NO se recomienda prohibir puntos/comas,
pero sí bloqueamos caracteres típicos de payloads (por ejemplo: < > ` ; $ | \\).

Ojo: esto complementa, no reemplaza, el uso de ORM/consultas parametrizadas (SQLAlchemy).
"""

from __future__ import annotations

import re


# Letras (Unicode) + espacios
REGEX_SOLO_LETRAS = re.compile(r"^[^\W\d_]+(?:\s+[^\W\d_]+)*$", re.UNICODE)

# Números
REGEX_SOLO_NUMEROS = re.compile(r"^\d+$")

# Alfanumérico + espacios (sin símbolos)
REGEX_ALFANUM_ESPACIO = re.compile(r"^[\w\d]+(?:\s+[\w\d]+)*$", re.UNICODE)

# Código de acceso (solo alfanumérico, sin espacios)
REGEX_CODIGO_ACCESO = re.compile(r"^[A-Za-z0-9]{4,32}$")

# Color hex #RRGGBB
REGEX_COLOR_HEX = re.compile(r"^#([A-Fa-f0-9]{6})$")

# Bloqueo simple para texto libre (evitar símbolos usados en payloads)
# Texto libre controlado: permite puntuación básica y comillas comunes.
REGEX_TEXTO_LIBRE_PERMITIDO = re.compile(
    r"^[\s\w\dÁÉÍÓÚÜÑáéíóúüñ.,:¡!¿?()\-\"\'’“”]+$",
    re.UNICODE,
)

# Caracteres que NO queremos en casi ningún input
CARACTERES_PELIGROSOS = set(['<', '>', '`', ';', '$', '|', '\\'])


def normalizar_espacios(v: str) -> str:
    """Trim + colapsa espacios múltiples."""
    v = (v or "").strip()
    v = re.sub(r"\s+", " ", v)
    return v


def requiere(v: str, min_len: int = 1) -> str:
    v = normalizar_espacios(v)
    if len(v) < min_len:
        raise ValueError(f"Debe tener al menos {min_len} caracteres")
    return v


def validar_solo_letras(v: str, min_len: int = 2) -> str:
    v = requiere(v, min_len=min_len)
    if not REGEX_SOLO_LETRAS.match(v):
        raise ValueError("Solo se permiten letras y espacios")
    return v


def validar_solo_numeros(v: str, min_len: int = 1, max_len: int | None = None) -> str:
    v = normalizar_espacios(v)
    if not v:
        raise ValueError("Campo obligatorio")
    if not REGEX_SOLO_NUMEROS.match(v):
        raise ValueError("Solo se permiten números")
    if len(v) < min_len:
        raise ValueError(f"Debe tener al menos {min_len} dígitos")
    if max_len is not None and len(v) > max_len:
        raise ValueError(f"No puede exceder {max_len} dígitos")
    return v


def validar_alfanum_espacio(v: str, min_len: int = 2) -> str:
    v = requiere(v, min_len=min_len)
    # \w incluye '_' por eso lo quitamos luego
    if "_" in v:
        raise ValueError("No se permite el caracter '_'")
    if not REGEX_ALFANUM_ESPACIO.match(v):
        raise ValueError("No se permiten caracteres especiales")
    return v


def validar_codigo_acceso(v: str) -> str:
    v = normalizar_espacios(v)
    if not v:
        return v
    if not REGEX_CODIGO_ACCESO.match(v):
        raise ValueError("Código inválido: solo letras/números, 4 a 32 caracteres")
    return v


def validar_color_hex(v: str) -> str:
    v = normalizar_espacios(v)
    if not REGEX_COLOR_HEX.match(v):
        raise ValueError("Color inválido, use formato #RRGGBB")
    return v


def validar_texto_libre(v: str, max_len: int = 2000) -> str:
    v = (v or "").strip()
    if not v:
        return v
    if len(v) > max_len:
        raise ValueError(f"Texto demasiado largo (máx {max_len} caracteres)")
    if any(ch in CARACTERES_PELIGROSOS for ch in v):
        raise ValueError("Texto contiene caracteres no permitidos")
    if not REGEX_TEXTO_LIBRE_PERMITIDO.match(v):
        raise ValueError("Texto contiene caracteres no permitidos")
    return v
