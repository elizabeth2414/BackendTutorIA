from sqlalchemy import Column, BigInteger, String, Boolean, DateTime, Text, Integer, ForeignKey, CheckConstraint
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.modelos import Base

class Recompensa(Base):
    __tablename__ = 'recompensa'
    
    id = Column(BigInteger, primary_key=True, index=True)
    nombre = Column(String(200), nullable=False)
    descripcion = Column(Text)
    tipo = Column(String(50), nullable=False)
    puntos_requeridos = Column(Integer)
    nivel_requerido = Column(Integer)
    lectura_id = Column(BigInteger, ForeignKey('contenido_lectura.id', ondelete='SET NULL'))
    imagen_url = Column(String(500))
    rareza = Column(String(20), default='comun')
    activo = Column(Boolean, default=True)
    fecha_creacion = Column(DateTime(timezone=True), server_default=func.now())
    
    __table_args__ = (
        CheckConstraint("tipo IN ('insignia', 'puntos', 'desbloqueo', 'avatar', 'trofeo')", name='check_tipo_recompensa'),
        CheckConstraint("rareza IN ('comun', 'raro', 'epico', 'legendario')", name='check_rareza_recompensa'),
    )