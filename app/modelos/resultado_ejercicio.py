from sqlalchemy import Column, BigInteger, String, DateTime, Float, Integer, Text, ForeignKey, CheckConstraint
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.modelos import Base

class ResultadoEjercicio(Base):
    __tablename__ = 'resultado_ejercicio'
    
    id = Column(BigInteger, primary_key=True, index=True)
    ejercicio_id = Column(BigInteger, ForeignKey('ejercicio_practica.id', ondelete='CASCADE'), nullable=False)
    puntuacion = Column(Float)
    audio_url = Column(String(500))
    retroalimentacion_ia = Column(Text)
    errores_corregidos = Column(Integer, default=0)
    tiempo_practica = Column(Integer)
    fecha_completacion = Column(DateTime(timezone=True), server_default=func.now())
    
    ejercicio = relationship("EjercicioPractica")
    
    __table_args__ = (
        CheckConstraint("puntuacion >= 0 AND puntuacion <= 100", name='check_puntuacion_resultado'),
    )