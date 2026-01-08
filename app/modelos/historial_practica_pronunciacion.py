from sqlalchemy import (
    Column, BigInteger, ForeignKey,
    Float, Integer, Text, DateTime
)
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from app.config import Base


class HistorialPracticaPronunciacion(Base):
    __tablename__ = "historial_practica_pronunciacion"

    id = Column(BigInteger, primary_key=True, index=True)

    estudiante_id = Column(
        BigInteger,
        ForeignKey("estudiante.id", ondelete="CASCADE"),
        nullable=False
    )

    ejercicio_id = Column(
        BigInteger,
        ForeignKey("ejercicio_practica.id", ondelete="CASCADE"),
        nullable=False
    )

    resultado_id = Column(
        BigInteger,
        ForeignKey("resultado_ejercicio.id", ondelete="SET NULL"),
        nullable=True
    )

    errores_detectados = Column(Integer)
    errores_corregidos = Column(Integer)

    puntuacion = Column(Float)
    tiempo_practica = Column(Integer)

    retroalimentacion_ia = Column(Text)

    fecha = Column(
        DateTime(timezone=True),
        server_default=func.now()
    )

    # -------------------------
    # RELACIONES
    # -------------------------
    estudiante = relationship("Estudiante")
    ejercicio = relationship("EjercicioPractica")
    resultado = relationship("ResultadoEjercicio")
