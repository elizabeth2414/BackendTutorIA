from sqlalchemy import (
    Column, BigInteger, ForeignKey,
    Float, Text, DateTime, JSON
)
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from app.config import Base


class HistorialPronunciacion(Base):
    __tablename__ = "historial_pronunciacion"

    id = Column(BigInteger, primary_key=True, index=True)

    estudiante_id = Column(
        BigInteger,
        ForeignKey("estudiante.id", ondelete="CASCADE"),
        nullable=False
    )

    contenido_id = Column(
        BigInteger,
        ForeignKey("contenido_lectura.id", ondelete="CASCADE"),
        nullable=False
    )

    evaluacion_id = Column(
        BigInteger,
        ForeignKey("evaluacion_lectura.id", ondelete="SET NULL"),
        nullable=True
    )

    puntuacion_global = Column(Float)
    velocidad = Column(Float)
    fluidez = Column(Float)
    precision_palabras = Column(Float)
    palabras_por_minuto = Column(Float)

    errores = Column(JSON)
    retroalimentacion_ia = Column(Text)

    fecha = Column(
        DateTime(timezone=True),
        server_default=func.now()
    )

    # -------------------------
    # RELACIONES
    # -------------------------
    estudiante = relationship("Estudiante")
    contenido = relationship("ContenidoLectura")
    evaluacion = relationship("EvaluacionLectura")
