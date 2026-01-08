from sqlalchemy import Column, BigInteger, String, DateTime, Float, JSON, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.modelos import Base

class AnalisisIA(Base):
    __tablename__ = 'analisis_ia'
    
    id = Column(BigInteger, primary_key=True, index=True)
    evaluacion_id = Column(BigInteger, ForeignKey('evaluacion_lectura.id', ondelete='CASCADE'), nullable=False)
    modelo_usado = Column(String(100))
    precision_global = Column(Float)
    palabras_detectadas = Column(JSON)
    errores_detectados = Column(JSON)
    tiempo_procesamiento = Column(Float)
    fecha_analisis = Column(DateTime(timezone=True), server_default=func.now())
    palabras_por_minuto = Column(Float)
    pausas_detectadas = Column(JSON)
    entonacion_score = Column(Float)
    ritmo_score = Column(Float)
    
    evaluacion = relationship("EvaluacionLectura")