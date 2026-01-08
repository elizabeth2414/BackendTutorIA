from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, BigInteger
from sqlalchemy.sql import func
from app.modelos import Base

class Usuario(Base):
    __tablename__ = 'usuario'
    
    id = Column(BigInteger, primary_key=True, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    nombre = Column(String(100), nullable=False)
    apellido = Column(String(100), nullable=False)
    fecha_creacion = Column(DateTime(timezone=True), server_default=func.now())
    activo = Column(Boolean, default=True)
    ultimo_login = Column(DateTime(timezone=True))
    intentos_login = Column(Integer, default=0)
    bloqueado = Column(Boolean, default=False)
    fecha_actualizacion = Column(DateTime(timezone=True), server_default=func.now())
    deleted_at = Column(DateTime(timezone=True), nullable=True)
    otp_secret = Column(String(255))
    otp_habilitado = Column(Boolean, default=False)