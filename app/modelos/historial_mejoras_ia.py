from sqlalchemy import (
    Column, BigInteger, ForeignKey,
    Float, String, DateTime
)
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from app.config import Base


class HistorialMejorasIA(Base):
    __tablename__ = "historial_mejoras_ia"

    id = Column(BigInteger, primary_key=True, index=True)

    estudiante_id = Column(
        BigInteger,
        ForeignKey("estudiante.id", ondelete="CASCADE"),
        nullable=False
    )

    palabra = Column(String(100))
    tipo_error = Column(String(50))

    precision_antes = Column(Float)
    precision_despues = Column(Float)

    fecha = Column(
        DateTime(timezone=True),
        server_default=func.now()
    )

    # -------------------------
    # RELACIONES
    # -------------------------
    estudiante = relationship("Estudiante")
