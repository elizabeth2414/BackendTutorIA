from sqlalchemy import Column, BigInteger, String, Boolean, DateTime, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.modelos import Base

class SesionUsuario(Base):
    __tablename__ = 'sesion_usuario'
    
    id = Column(BigInteger, primary_key=True, index=True)
    usuario_id = Column(BigInteger, ForeignKey('usuario.id', ondelete='CASCADE'), nullable=False)
    token_sesion = Column(String(500), unique=True, nullable=False)
    fecha_inicio = Column(DateTime(timezone=True), server_default=func.now())
    fecha_expiracion = Column(DateTime(timezone=True), nullable=False)
    ip_address = Column(String(50))
    dispositivo = Column(String(200))
    activa = Column(Boolean, default=True)
    
    usuario = relationship("Usuario")