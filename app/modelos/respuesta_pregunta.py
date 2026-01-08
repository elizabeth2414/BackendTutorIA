from sqlalchemy import Column, BigInteger, Text, Boolean, Integer, ForeignKey
from sqlalchemy.orm import relationship
from app.modelos import Base

class RespuestaPregunta(Base):
    __tablename__ = 'respuesta_pregunta'
    
    id = Column(BigInteger, primary_key=True, index=True)
    progreso_id = Column(BigInteger, ForeignKey('progreso_actividad.id', ondelete='CASCADE'), nullable=False)
    pregunta_id = Column(BigInteger, ForeignKey('pregunta.id', ondelete='CASCADE'), nullable=False)
    respuesta_estudiante = Column(Text)
    correcta = Column(Boolean)
    puntuacion_obtenida = Column(Integer)
    tiempo_respuesta = Column(Integer)
    
    progreso = relationship("ProgresoActividad")
    pregunta = relationship("Pregunta")