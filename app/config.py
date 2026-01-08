# app/config.py

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base

from app import settings  # <- settings viene de app/__init__.py

# 1. Cargar la URL desde .env
SQLALCHEMY_DATABASE_URL = settings.DATABASE_URL

# 2. Crear engine
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    future=True
)

# 3. Crear sesión de conexión
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

# 4. Base de modelos
Base = declarative_base()


# 5. Dependency para FastAPI
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
