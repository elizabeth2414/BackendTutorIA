from sqlalchemy import Column, BigInteger, String, Boolean, DateTime, Date, Text, Integer, JSON, ForeignKey, CheckConstraint
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.modelos import Base

class Estudiante(Base):
    __tablename__ = "estudiante"

    id = Column(BigInteger, primary_key=True, index=True)

    usuario_id = Column(BigInteger, ForeignKey("usuario.id", ondelete="SET NULL"), unique=True, nullable=True)
    docente_id = Column(BigInteger, ForeignKey("docente.id", ondelete="RESTRICT"), nullable=False)
    padre_id = Column(BigInteger, ForeignKey("padre.id", ondelete="SET NULL"), nullable=True)

    nombre = Column(String(100), nullable=False)
    apellido = Column(String(100), nullable=False)
    fecha_nacimiento = Column(Date, nullable=False)
    nivel_educativo = Column(Integer, nullable=False)
    necesidades_especiales = Column(Text)

    avatar_url = Column(String(500))
    configuracion = Column(JSON, server_default='{"sonidos": true, "animaciones": true, "dificultad": "media"}')

    creado_en = Column(DateTime(timezone=True), server_default=func.now())
    activo = Column(Boolean, default=True)
    deleted_at = Column(DateTime(timezone=True), nullable=True)
    transferible = Column(Boolean, default=True)

    usuario = relationship("Usuario", backref="estudiante")
    docente = relationship("Docente", backref="estudiantes")
    padre = relationship("Padre", backref="hijos")

    __table_args__ = (
        CheckConstraint("nivel_educativo BETWEEN 1 AND 6", name="check_nivel_educativo"),
    )
