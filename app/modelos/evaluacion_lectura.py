from sqlalchemy import Column, BigInteger, String, Boolean, DateTime, Text, Integer, Float, ForeignKey, CheckConstraint
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.modelos import Base

class EvaluacionLectura(Base):
    __tablename__ = 'evaluacion_lectura'
    
    id = Column(BigInteger, primary_key=True, index=True)
    estudiante_id = Column(BigInteger, ForeignKey('estudiante.id', ondelete='CASCADE'), nullable=False)
    contenido_id = Column(BigInteger, ForeignKey('contenido_lectura.id', ondelete='CASCADE'), nullable=False)
    fecha_evaluacion = Column(DateTime(timezone=True), server_default=func.now())
    puntuacion_pronunciacion = Column(Float)
    velocidad_lectura = Column(Float)
    fluidez = Column(Float)
    precision_palabras = Column(Float)
    retroalimentacion_ia = Column(Text)
    audio_url = Column(String(500))
    duracion_audio = Column(Integer)
    estado = Column(String(20), default='completado')
    deleted_at = Column(DateTime(timezone=True), nullable=True)
    
    estudiante = relationship("Estudiante")
    contenido = relationship("ContenidoLectura")
    
    __table_args__ = (
        CheckConstraint("puntuacion_pronunciacion >= 0 AND puntuacion_pronunciacion <= 100", name='check_puntuacion_pronunciacion'),
        CheckConstraint("estado IN ('completado', 'en_progreso', 'cancelado')", name='check_estado_evaluacion'),
    )