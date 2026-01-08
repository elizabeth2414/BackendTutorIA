from sqlalchemy import Column, BigInteger, String, DateTime, ForeignKey, UniqueConstraint, CheckConstraint
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.modelos import Base

class EstudianteCurso(Base):
    __tablename__ = 'estudiante_curso'
    
    id = Column(BigInteger, primary_key=True, index=True)
    estudiante_id = Column(BigInteger, ForeignKey('estudiante.id', ondelete='CASCADE'), nullable=False)
    curso_id = Column(BigInteger, ForeignKey('curso.id', ondelete='CASCADE'), nullable=False)
    fecha_inscripcion = Column(DateTime(timezone=True), server_default=func.now())
    estado = Column(String(20), default='activo')
    
    estudiante = relationship("Estudiante")
    curso = relationship("Curso")
    
    __table_args__ = (
        UniqueConstraint('estudiante_id', 'curso_id', name='uq_estudiante_curso'),
        CheckConstraint("estado IN ('activo', 'inactivo', 'suspendido')", name='check_estado_curso'),
    )