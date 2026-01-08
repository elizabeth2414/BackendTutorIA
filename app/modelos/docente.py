from sqlalchemy import Column, BigInteger, String, Boolean, DateTime, Date, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.modelos import Base

class Docente(Base):
    __tablename__ = 'docente'
    
    id = Column(BigInteger, primary_key=True, index=True)
    usuario_id = Column(BigInteger, ForeignKey('usuario.id', ondelete='CASCADE'), unique=True, nullable=False)
    especialidad = Column(String(100))
    grado_academico = Column(String(100))
    institucion = Column(String(200))
    fecha_contratacion = Column(Date)
    creado_en = Column(DateTime(timezone=True), server_default=func.now())
    activo = Column(Boolean, default=True)
    
    usuario = relationship("Usuario")