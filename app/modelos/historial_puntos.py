from sqlalchemy import Column, BigInteger, String, DateTime, Integer, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.modelos import Base

class HistorialPuntos(Base):
    __tablename__ = 'historial_puntos'
    
    id = Column(BigInteger, primary_key=True, index=True)
    estudiante_id = Column(BigInteger, ForeignKey('estudiante.id', ondelete='CASCADE'), nullable=False)
    motivo = Column(String(200))
    puntos = Column(Integer)
    fecha = Column(DateTime(timezone=True), server_default=func.now())
    
    estudiante = relationship("Estudiante")