from sqlalchemy import Column, BigInteger, String, DateTime, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.modelos import Base

class ContrasenaAnterior(Base):
    __tablename__ = 'contrasena_anterior'
    
    id = Column(BigInteger, primary_key=True, index=True)
    usuario_id = Column(BigInteger, ForeignKey('usuario.id', ondelete='CASCADE'), nullable=False)
    password_hash_old = Column(String(255), nullable=False)
    fecha_cambio = Column(DateTime(timezone=True), server_default=func.now())
    
    usuario = relationship("Usuario")