from sqlalchemy import Column, BigInteger, String, Boolean, DateTime, Text, Integer, JSON, ForeignKey, CheckConstraint
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.modelos import Base


class ContenidoLectura(Base):
    __tablename__ = 'contenido_lectura'
    
    id = Column(BigInteger, primary_key=True, index=True)

    # Relaciones opcionales
    curso_id = Column(BigInteger, ForeignKey('curso.id', ondelete='SET NULL'))
    docente_id = Column(BigInteger, ForeignKey('docente.id', ondelete='SET NULL'))
    categoria_id = Column(BigInteger, ForeignKey('categoria_lectura.id', ondelete='SET NULL'))

    # Datos base
    titulo = Column(String(300), nullable=False)
    contenido = Column(Text, nullable=False)

    # Multimedia
    audio_url = Column(String(500))
    duracion_audio = Column(Integer)

    # Metadatos
    nivel_dificultad = Column(Integer, nullable=False)
    edad_recomendada = Column(Integer, nullable=False)
    palabras_clave = Column(ARRAY(Text))
    etiquetas = Column(JSON, server_default='[]')

    por_defecto = Column(Boolean, default=False)
    publico = Column(Boolean, default=False)

    # Tiempos
    fecha_creacion = Column(DateTime(timezone=True), server_default=func.now())
    fecha_actualizacion = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now()
    )

    activo = Column(Boolean, default=True)
    deleted_at = Column(DateTime(timezone=True), nullable=True)

    # Relaciones ORM
    curso = relationship("Curso")
    docente = relationship("Docente")
    categoria = relationship("CategoriaLectura")

    # RELACIÓN CON ACTIVIDADES GENERADAS POR IA
    actividades = relationship(
        "Actividad",
        back_populates="contenido",
        cascade="all, delete-orphan"
    )

    __table_args__ = (
        CheckConstraint("nivel_dificultad BETWEEN 1 AND 5", name='check_nivel_dificultad'),
        CheckConstraint("edad_recomendada BETWEEN 5 AND 12", name='check_edad_recomendada'),
    )
