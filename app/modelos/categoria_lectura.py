from sqlalchemy import Column, BigInteger, String, Boolean, DateTime, Text, Integer, CheckConstraint
from sqlalchemy.sql import func
from app.modelos import Base

class CategoriaLectura(Base):
    __tablename__ = 'categoria_lectura'
    
    id = Column(BigInteger, primary_key=True, index=True)
    nombre = Column(String(200), nullable=False)
    descripcion = Column(Text)
    edad_minima = Column(Integer, nullable=False)
    edad_maxima = Column(Integer, nullable=False)
    color = Column(String(7), default='#3498db')
    icono = Column(String(100))
    activo = Column(Boolean, default=True)
    creado_en = Column(DateTime(timezone=True), server_default=func.now())
    deleted_at = Column(DateTime(timezone=True), nullable=True)
    
    __table_args__ = (
        CheckConstraint("edad_minima >= 5", name='check_edad_minima'),
        CheckConstraint("edad_maxima <= 12", name='check_edad_maxima'),
        CheckConstraint("edad_maxima >= edad_minima", name='check_edad_rango'),
    )