from sqlalchemy import Column, BigInteger, String, Integer, Float, ForeignKey, CheckConstraint
from sqlalchemy.orm import relationship
from app.modelos import Base

class DetalleEvaluacion(Base):
    __tablename__ = 'detalle_evaluacion'
    
    id = Column(BigInteger, primary_key=True, index=True)
    evaluacion_id = Column(BigInteger, ForeignKey('evaluacion_lectura.id', ondelete='CASCADE'), nullable=False)
    palabra = Column(String(100), nullable=False)
    posicion_en_texto = Column(Integer, nullable=False)
    precision_pronunciacion = Column(Float)
    retroalimentacion_palabra = Column(String(300))
    timestamp_inicio = Column(Float)
    timestamp_fin = Column(Float)
    tipo_tokenizacion = Column(String(50))
    
    evaluacion = relationship("EvaluacionLectura")
    
    __table_args__ = (
        CheckConstraint("precision_pronunciacion >= 0 AND precision_pronunciacion <= 100", name='check_precision_palabra'),
    )