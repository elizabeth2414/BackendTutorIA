from sqlalchemy import Column, BigInteger, String, DateTime, Boolean, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.modelos import Base


class PasswordResetToken(Base):
    """
    Modelo para tokens de reset de contraseña.

    Características:
    - Tokens únicos y seguros generados con secrets
    - Expiración automática (default: 1 hora)
    - Un solo uso (se marca como usado después)
    - Vinculado a un usuario específico
    - Permite invalidar tokens antiguos
    """
    __tablename__ = 'password_reset_token'

    id = Column(BigInteger, primary_key=True, index=True)
    usuario_id = Column(
        BigInteger,
        ForeignKey('usuario.id', ondelete='CASCADE'),
        nullable=False,
        index=True
    )
    token = Column(String(255), unique=True, nullable=False, index=True)
    fecha_creacion = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    fecha_expiracion = Column(DateTime(timezone=True), nullable=False)
    usado = Column(Boolean, default=False, nullable=False)
    fecha_uso = Column(DateTime(timezone=True), nullable=True)
    ip_solicitante = Column(String(50), nullable=True)

    # Relationship
    usuario = relationship("Usuario", backref="password_reset_tokens")
