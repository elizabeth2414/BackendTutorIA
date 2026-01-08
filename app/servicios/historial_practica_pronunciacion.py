from sqlalchemy.orm import Session

from app.modelos.historial_practica_pronunciacion import (
    HistorialPracticaPronunciacion
)
from app.esquemas.historial_practica_pronunciacion import (
    HistorialPracticaPronunciacionCreate
)


def crear_historial_practica_pronunciacion(
    db: Session,
    data: HistorialPracticaPronunciacionCreate
) -> HistorialPracticaPronunciacion:

    historial = HistorialPracticaPronunciacion(
        estudiante_id=data.estudiante_id,
        ejercicio_id=data.ejercicio_id,
        resultado_id=data.resultado_id,
        errores_detectados=data.errores_detectados,
        errores_corregidos=data.errores_corregidos,
        puntuacion=data.puntuacion,
        tiempo_practica=data.tiempo_practica,
        retroalimentacion_ia=data.retroalimentacion_ia
    )

    db.add(historial)
    db.commit()
    db.refresh(historial)

    return historial
