# app/settings.py

from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    """
    Configuración de la aplicación usando variables de entorno.

    IMPORTANTE:
    - Crea un archivo .env basado en .env.example
    - NUNCA subas el archivo .env al repositorio
    - Genera una SECRET_KEY única y segura
    """

    # ============================================
    # SEGURIDAD - JWT
    # ============================================
    # ⚠️ CRÍTICO: Esta clave debe ser secreta y única
    # Genera una con: python -c "import secrets; print(secrets.token_urlsafe(32))"
    SECRET_KEY: str  # Sin valor por defecto - DEBE estar en .env

    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    # ============================================
    # BASE DE DATOS
    # ============================================
    DATABASE_URL: str  # Sin valor por defecto - DEBE estar en .env

    # ============================================
    # IA Y MODELOS
    # ============================================
    WHISPER_MODEL: str = "small"

    # ============================================
    # SERVIDOR (Opcional)
    # ============================================
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    ENVIRONMENT: str = "development"

    # ============================================
    # CORS (Opcional)
    # ============================================
    CORS_ORIGINS: Optional[str] = None

    # ============================================
    # EMAIL (Opcional - para futuras features)
    # ============================================
    SMTP_HOST: Optional[str] = None
    SMTP_PORT: Optional[int] = None
    SMTP_USER: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    SMTP_FROM: Optional[str] = None

    # ============================================
    # ARCHIVOS
    # ============================================
    UPLOAD_DIR: str = "./uploads"
    MAX_FILE_SIZE_MB: int = 10

    # ============================================
    # LOGGING
    # ============================================
    LOG_LEVEL: str = "INFO"
    LOG_DIR: str = "./logs"

    class Config:
        env_file = ".env"
        extra = "ignore"
        case_sensitive = True


# Instancia global de configuración
settings = Settings()
