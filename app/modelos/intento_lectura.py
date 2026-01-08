from sqlalchemy import Column, Integer, Float, String, ForeignKey, DateTime
from sqlalchemy.sql import func
from app.config import Base


class IntentoLectura(Base):
    __tablename__ = "intento_lectura"

    id = Column(Integer, primary_key=True, index=True)
    evaluacion_id = Column(
        Integer,
        ForeignKey("evaluacion_lectura.id", ondelete="CASCADE"),
        nullable=False,
    )

    numero_intento = Column(Integer, default=1)
    puntuacion_pronunciacion = Column(Float, nullable=True)
    velocidad_lectura = Column(Float, nullable=True)
    fluidez = Column(Float, nullable=True)
    audio_url = Column(String(500), nullable=True)
    fecha_intento = Column(DateTime(timezone=True), server_default=func.now())
