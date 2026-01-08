from sqlalchemy.orm import Session

from app.modelos.historial_pronunciacion import HistorialPronunciacion
from app.esquemas.historial_pronunciacion import (
    HistorialPronunciacionCreate
)


def crear_historial_pronunciacion(
    db: Session,
    data: HistorialPronunciacionCreate
) -> HistorialPronunciacion:

    historial = HistorialPronunciacion(
        estudiante_id=data.estudiante_id,
        contenido_id=data.contenido_id,
        evaluacion_id=data.evaluacion_id,
        puntuacion_global=data.puntuacion_global,
        velocidad=data.velocidad,
        fluidez=data.fluidez,
        precision_palabras=data.precision_palabras,
        palabras_por_minuto=data.palabras_por_minuto,
        errores=data.errores,
        retroalimentacion_ia=data.retroalimentacion_ia
    )

    db.add(historial)
    db.commit()
    db.refresh(historial)

    return historial
