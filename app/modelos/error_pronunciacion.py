from sqlalchemy import Column, BigInteger, String, Integer, Float, Text, ForeignKey, CheckConstraint
from sqlalchemy.orm import relationship
from app.modelos import Base

class ErrorPronunciacion(Base):
    __tablename__ = 'error_pronunciacion'
    
    id = Column(BigInteger, primary_key=True, index=True)
    detalle_evaluacion_id = Column(BigInteger, ForeignKey('detalle_evaluacion.id', ondelete='CASCADE'), nullable=False)
    tipo_error = Column(String(50), nullable=False)
    palabra_original = Column(String(100))
    palabra_detectada = Column(String(100))
    timestamp_inicio = Column(Float)
    timestamp_fin = Column(Float)
    severidad = Column(Integer)
    sugerencia_correccion = Column(Text)
    
    detalle = relationship("DetalleEvaluacion")
    
    __table_args__ = (
        CheckConstraint("tipo_error IN ('sustitucion', 'omision', 'insercion', 'puntuacion', 'entonacion', 'velocidad', 'fluidez')", name='check_tipo_error'),
        CheckConstraint("severidad >= 1 AND severidad <= 5", name='check_severidad'),
    )