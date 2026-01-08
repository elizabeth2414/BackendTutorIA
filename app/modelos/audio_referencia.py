from sqlalchemy import Column, BigInteger, String, DateTime, Integer, Text, ForeignKey, CheckConstraint
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.modelos import Base

class AudioReferencia(Base):
    __tablename__ = 'audio_referencia'
    
    id = Column(BigInteger, primary_key=True, index=True)
    contenido_id = Column(BigInteger, ForeignKey('contenido_lectura.id', ondelete='CASCADE'), nullable=False)
    audio_url = Column(String(500), nullable=False)
    duracion = Column(Integer, nullable=False)
    tipo = Column(String(20))
    transcripcion = Column(Text)
    fecha_creacion = Column(DateTime(timezone=True), server_default=func.now())
    
    contenido = relationship("ContenidoLectura")
    
    __table_args__ = (
        CheckConstraint("tipo IN ('sistema', 'docente', 'profesional')", name='check_tipo_audio'),
    )