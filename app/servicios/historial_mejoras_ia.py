from sqlalchemy.orm import Session

from app.modelos.historial_mejoras_ia import HistorialMejorasIA
from app.esquemas.historial_mejoras_ia import HistorialMejorasIACreate


def registrar_mejora_ia(
    db: Session,
    data: HistorialMejorasIACreate
) -> HistorialMejorasIA:

    mejora = HistorialMejorasIA(
        estudiante_id=data.estudiante_id,
        palabra=data.palabra,
        tipo_error=data.tipo_error,
        precision_antes=data.precision_antes,
        precision_despues=data.precision_despues
    )

    db.add(mejora)
    db.commit()
    db.refresh(mejora)

    return mejora
