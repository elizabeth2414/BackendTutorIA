from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, BigInteger
from sqlalchemy.sql import func
from app.modelos import Base
from sqlalchemy.orm import relationship


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
    roles = relationship("UsuarioRol", back_populates="usuario", passive_deletes=True)
    sesiones = relationship("SesionUsuario", back_populates="usuario", passive_deletes=True)

    # Verificación de email
    email_verificado = Column(Boolean, default=False, nullable=False)
    token_verificacion = Column(String(255), nullable=True, index=True)
    token_verificacion_expira = Column(DateTime(timezone=True), nullable=True)
    
    # Reset de contraseña
    token_reset_password = Column(String(255), nullable=True, index=True)
    token_reset_expira = Column(DateTime(timezone=True), nullable=True)
    token_reset_usado = Column(Boolean, default=False)
    token_reset_ip = Column(String(50), nullable=True)