from sqlalchemy import Column, BigInteger, String, Boolean, DateTime, Text, Integer, JSON, ForeignKey, CheckConstraint
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.modelos import Base

class Curso(Base):
    __tablename__ = 'curso'
    
    id = Column(BigInteger, primary_key=True, index=True)
    docente_id = Column(BigInteger, ForeignKey('docente.id', ondelete='CASCADE'), nullable=False)
    nombre = Column(String(200), nullable=False)
    descripcion = Column(Text)
    nivel = Column(Integer, nullable=False)
    codigo_acceso = Column(String(50), unique=True)
    fecha_creacion = Column(DateTime(timezone=True), server_default=func.now())
    activo = Column(Boolean, default=True)
    configuracion = Column(JSON, server_default='{"max_estudiantes": 30, "publico": false}')
    deleted_at = Column(DateTime(timezone=True), nullable=True)
    
    docente = relationship("Docente")
    
    __table_args__ = (
        CheckConstraint("nivel BETWEEN 1 AND 6", name='check_nivel_curso'),
    )