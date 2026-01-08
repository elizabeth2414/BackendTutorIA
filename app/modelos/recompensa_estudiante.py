from sqlalchemy import Column, BigInteger, Boolean, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.modelos import Base

class RecompensaEstudiante(Base):
    __tablename__ = 'recompensa_estudiante'
    
    id = Column(BigInteger, primary_key=True, index=True)
    estudiante_id = Column(BigInteger, ForeignKey('estudiante.id', ondelete='CASCADE'), nullable=False)
    recompensa_id = Column(BigInteger, ForeignKey('recompensa.id', ondelete='CASCADE'), nullable=False)
    fecha_obtencion = Column(DateTime(timezone=True), server_default=func.now())
    visto = Column(Boolean, default=False)
    
    estudiante = relationship("Estudiante")
    recompensa = relationship("Recompensa")
    
    __table_args__ = (
        UniqueConstraint('estudiante_id', 'recompensa_id', name='uq_estudiante_recompensa'),
    )