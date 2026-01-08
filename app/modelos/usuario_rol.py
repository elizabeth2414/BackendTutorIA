from sqlalchemy import Column, BigInteger, String, Boolean, DateTime, ForeignKey, CheckConstraint
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.modelos import Base

class UsuarioRol(Base):
    __tablename__ = 'usuario_rol'
    
    id = Column(BigInteger, primary_key=True, index=True)
    usuario_id = Column(BigInteger, ForeignKey('usuario.id', ondelete='CASCADE'), nullable=False)
    rol = Column(String(50), nullable=False)
    fecha_asignacion = Column(DateTime(timezone=True), server_default=func.now())
    fecha_expiracion = Column(DateTime(timezone=True), nullable=True)
    activo = Column(Boolean, default=True)
    
    usuario = relationship("Usuario")
    
    __table_args__ = (
        CheckConstraint("rol IN ('estudiante', 'docente', 'padre', 'admin')", name='check_rol_valido'),
    )