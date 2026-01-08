from sqlalchemy import Column, BigInteger, String, Boolean, DateTime, Text, Integer, ForeignKey, CheckConstraint
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.modelos import Base

class EjercicioPractica(Base):
    __tablename__ = 'ejercicio_practica'
    
    id = Column(BigInteger, primary_key=True, index=True)
    estudiante_id = Column(BigInteger, ForeignKey('estudiante.id', ondelete='CASCADE'), nullable=False)
    evaluacion_id = Column(BigInteger, ForeignKey('evaluacion_lectura.id', ondelete='CASCADE'), nullable=False)
    tipo_ejercicio = Column(String(50), nullable=False)
    palabras_objetivo = Column(ARRAY(Text), nullable=False)
    texto_practica = Column(Text, nullable=False)
    dificultad = Column(Integer)
    completado = Column(Boolean, default=False)
    intentos = Column(Integer, default=0)
    fecha_creacion = Column(DateTime(timezone=True), server_default=func.now())
    fecha_completacion = Column(DateTime(timezone=True))
    deleted_at = Column(DateTime(timezone=True), nullable=True)
    
    estudiante = relationship("Estudiante")
    evaluacion = relationship("EvaluacionLectura")
    
    __table_args__ = (
        CheckConstraint("tipo_ejercicio IN ('palabras_aisladas', 'oraciones', 'ritmo', 'entonacion', 'puntuacion')", name='check_tipo_ejercicio'),
        CheckConstraint("dificultad BETWEEN 1 AND 3", name='check_dificultad_ejercicio'),
    )