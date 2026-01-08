from sqlalchemy import Column, BigInteger, String, Boolean, DateTime, ForeignKey, CheckConstraint
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.modelos import Base

class Padre(Base):
    __tablename__ = 'padre'
    
    id = Column(BigInteger, primary_key=True, index=True)
    usuario_id = Column(BigInteger, ForeignKey('usuario.id', ondelete='SET NULL'), unique=True)
    telefono_contacto = Column(String(20))
    parentesco = Column(String(20))
    notificaciones_activas = Column(Boolean, default=True)
    creado_en = Column(DateTime(timezone=True), server_default=func.now())
    activo = Column(Boolean, default=True)
    deleted_at = Column(DateTime(timezone=True), nullable=True)
    
    usuario = relationship("Usuario")
    
    __table_args__ = (
        CheckConstraint("parentesco IN ('padre', 'madre', 'tutor', 'otro')", name='check_parentesco_valido'),
    )