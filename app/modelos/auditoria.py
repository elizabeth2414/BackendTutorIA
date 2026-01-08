from sqlalchemy import Column, BigInteger, String, DateTime, Text, JSON, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.modelos import Base

class Auditoria(Base):
    __tablename__ = 'auditoria'
    
    id = Column(BigInteger, primary_key=True, index=True)
    usuario_id = Column(BigInteger, ForeignKey('usuario.id', ondelete='SET NULL'))
    accion = Column(String(100), nullable=False)
    tabla_afectada = Column(String(100))
    registro_id = Column(BigInteger)
    datos_anteriores = Column(JSON)
    datos_nuevos = Column(JSON)
    ip_address = Column(String(50))
    user_agent = Column(Text)
    fecha_evento = Column(DateTime(timezone=True), server_default=func.now())
    
    usuario = relationship("Usuario")