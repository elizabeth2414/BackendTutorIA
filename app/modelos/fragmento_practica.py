from sqlalchemy import Column, BigInteger, Text, Integer, String, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from app.modelos import Base

class FragmentoPractica(Base):
    __tablename__ = 'fragmento_practica'
    
    id = Column(BigInteger, primary_key=True, index=True)
    ejercicio_id = Column(BigInteger, ForeignKey('ejercicio_practica.id', ondelete='CASCADE'), nullable=False)
    texto_fragmento = Column(Text, nullable=False)
    posicion_inicio = Column(Integer, nullable=False)
    posicion_fin = Column(Integer, nullable=False)
    tipo_error_asociado = Column(String(50))
    completado = Column(Boolean, default=False)
    mejora_lograda = Column(Boolean, default=False)
    
    ejercicio = relationship("EjercicioPractica")