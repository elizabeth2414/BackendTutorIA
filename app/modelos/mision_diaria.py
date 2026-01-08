from sqlalchemy import Column, BigInteger, String, Boolean, DateTime, Integer, Date, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.modelos import Base

class MisionDiaria(Base):
    __tablename__ = 'mision_diaria'
    
    id = Column(BigInteger, primary_key=True, index=True)
    estudiante_id = Column(BigInteger, ForeignKey('estudiante.id', ondelete='CASCADE'), nullable=False)
    tipo_mision = Column(String(100))
    objetivo = Column(Integer)
    progreso = Column(Integer, default=0)
    completada = Column(Boolean, default=False)
    recompensa_puntos = Column(Integer, default=50)
    fecha = Column(Date, server_default=func.current_date())
    
    estudiante = relationship("Estudiante")