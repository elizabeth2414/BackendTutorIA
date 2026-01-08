from sqlalchemy import Column, BigInteger, Text, String, Integer, JSON, ForeignKey, CheckConstraint
from sqlalchemy.orm import relationship
from app.modelos import Base

class Pregunta(Base):
    __tablename__ = 'pregunta'
    
    id = Column(BigInteger, primary_key=True, index=True)
    actividad_id = Column(BigInteger, ForeignKey('actividad.id', ondelete='CASCADE'), nullable=False)
    texto_pregunta = Column(Text, nullable=False)
    tipo_respuesta = Column(String(50), nullable=False)
    opciones = Column(JSON)
    respuesta_correcta = Column(Text)
    puntuacion = Column(Integer, nullable=False)
    explicacion = Column(Text)
    orden = Column(Integer, default=1)
    
    actividad = relationship("Actividad", back_populates="preguntas")   # ← ✔ CORREGIDO
    
    __table_args__ = (
        CheckConstraint("tipo_respuesta IN ('multiple_choice', 'verdadero_falso', 'texto_libre', 'emparejamiento')", name='check_tipo_respuesta'),
        CheckConstraint("puntuacion > 0", name='check_puntuacion_pregunta'),
    )