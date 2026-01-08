from sqlalchemy import Column, BigInteger, String, Boolean, DateTime, Text, Integer, ForeignKey
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.modelos import Base

class ActividadLectura(Base):
    __tablename__ = 'actividad_lectura'

    id = Column(BigInteger, primary_key=True, index=True)
    lectura_id = Column(BigInteger, ForeignKey('contenido_lectura.id', ondelete='CASCADE'), nullable=False, index=True)
    tipo = Column(String(50), nullable=False)
    enunciado = Column(Text, nullable=False)
    opciones = Column(JSONB)
    respuesta_correcta = Column(Text)
    explicacion = Column(Text)
    edad_min = Column(Integer, default=7)
    edad_max = Column(Integer, default=10)
    dificultad = Column(String(20), default='media')
    origen = Column(String(20), default='ia', nullable=False)
    activo = Column(Boolean, default=True)
    creado_en = Column(DateTime(timezone=True), server_default=func.now())

    # Relación con ContenidoLectura
    lectura = relationship("ContenidoLectura", backref="actividades_lectura")
