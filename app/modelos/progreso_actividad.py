from sqlalchemy import Column, BigInteger, Boolean, DateTime, Integer, Float, JSON, ForeignKey, UniqueConstraint, CheckConstraint
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.modelos import Base

class ProgresoActividad(Base):
    __tablename__ = 'progreso_actividad'
    
    id = Column(BigInteger, primary_key=True, index=True)
    estudiante_id = Column(BigInteger, ForeignKey('estudiante.id', ondelete='CASCADE'), nullable=False)
    actividad_id = Column(BigInteger, ForeignKey('actividad.id', ondelete='CASCADE'), nullable=False)
    puntuacion = Column(Float, nullable=False)
    fecha_completacion = Column(DateTime(timezone=True), server_default=func.now())
    intentos = Column(Integer, default=1)
    tiempo_completacion = Column(Integer)
    errores_cometidos = Column(Integer, default=0)
    respuestas = Column(JSON)
    deleted_at = Column(DateTime(timezone=True), nullable=True)
    
    estudiante = relationship("Estudiante")
    actividad = relationship("Actividad")
    
    __table_args__ = (
        UniqueConstraint('estudiante_id', 'actividad_id', name='uq_estudiante_actividad'),
        CheckConstraint("puntuacion >= 0", name='check_puntuacion_progreso'),
    )