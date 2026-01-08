from sqlalchemy import Column, BigInteger, String, Boolean, DateTime, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.modelos import Base

class AccesoPadre(Base):
    __tablename__ = 'acceso_padre'
    
    id = Column(BigInteger, primary_key=True, index=True)
    estudiante_id = Column(BigInteger, ForeignKey('estudiante.id', ondelete='CASCADE'), nullable=False)
    padre_id = Column(BigInteger, ForeignKey('padre.id', ondelete='SET NULL'))
    email_padre = Column(String(255))
    rol_padre = Column(String(50), default='padre')
    puede_ver_progreso = Column(Boolean, default=True)
    creado_en = Column(DateTime(timezone=True), server_default=func.now())
    
    estudiante = relationship("Estudiante")
    padre = relationship("Padre")