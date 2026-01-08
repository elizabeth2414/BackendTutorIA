from sqlalchemy import Column, BigInteger, Integer, DateTime, ForeignKey, CheckConstraint
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.modelos import Base

class NivelEstudiante(Base):
    __tablename__ = 'nivel_estudiante'
    
    id = Column(BigInteger, primary_key=True, index=True)
    estudiante_id = Column(BigInteger, ForeignKey('estudiante.id', ondelete='CASCADE'), unique=True, nullable=False)
    nivel_actual = Column(Integer, default=1)
    puntos_totales = Column(Integer, default=0)
    puntos_nivel_actual = Column(Integer, default=0)
    puntos_para_siguiente_nivel = Column(Integer, default=1000)
    lecturas_completadas = Column(Integer, default=0)
    actividades_completadas = Column(Integer, default=0)
    racha_actual = Column(Integer, default=0)
    racha_maxima = Column(Integer, default=0)
    fecha_actualizacion = Column(DateTime(timezone=True), server_default=func.now())
    
    estudiante = relationship("Estudiante")
    
    __table_args__ = (
        CheckConstraint("nivel_actual >= 1", name='check_nivel_actual'),
        CheckConstraint("puntos_totales >= 0", name='check_puntos_totales'),
    )