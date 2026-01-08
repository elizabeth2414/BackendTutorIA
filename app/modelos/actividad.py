from sqlalchemy import (
    Column, BigInteger, String, Boolean, DateTime, Text, Integer, JSON, ForeignKey
)
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from app.modelos import Base


class Actividad(Base):
    __tablename__ = "actividad"

    id = Column(BigInteger, primary_key=True, index=True)
    contenido_id = Column(
        BigInteger,
        ForeignKey("contenido_lectura.id", ondelete="CASCADE"),
        nullable=False
    )
    tipo = Column(String(50), nullable=False)  # 'preguntas', 'multiple_choice', etc.
    titulo = Column(String(200), nullable=False)
    descripcion = Column(Text)
    configuracion = Column(JSON, nullable=False, default=dict)
    puntos_maximos = Column(Integer, nullable=False)
    tiempo_estimado = Column(Integer)
    dificultad = Column(Integer)
    activo = Column(Boolean, default=True)
    fecha_creacion = Column(DateTime(timezone=True), server_default=func.now())
    deleted_at = Column(DateTime(timezone=True), nullable=True)

    contenido = relationship("ContenidoLectura", back_populates="actividades")
    preguntas = relationship(
        "Pregunta",
        back_populates="actividad",
        cascade="all, delete-orphan"
    )

