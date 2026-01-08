from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from typing import List, Optional
from datetime import date

from app.modelos import Recompensa, RecompensaEstudiante, MisionDiaria, HistorialPuntos, NivelEstudiante, Estudiante
from app.esquemas.gamificacion import RecompensaCreate, RecompensaEstudianteCreate, MisionDiariaCreate, HistorialPuntosCreate
from app.logs.logger import logger

def crear_recompensa(db: Session, recompensa: RecompensaCreate):
    db_recompensa = Recompensa(**recompensa.dict())
    db.add(db_recompensa)
    db.commit()
    db.refresh(db_recompensa)
    return db_recompensa

def obtener_recompensas(db: Session, skip: int = 0, limit: int = 100, activo: Optional[bool] = None):
    query = db.query(Recompensa)
    if activo is not None:
        query = query.filter(Recompensa.activo == activo)
    return query.offset(skip).limit(limit).all()

def obtener_recompensa(db: Session, recompensa_id: int):
    return db.query(Recompensa).filter(Recompensa.id == recompensa_id).first()

def asignar_recompensa_estudiante(db: Session, asignacion: RecompensaEstudianteCreate):
    # Verificar si ya tiene la recompensa
    existente = db.query(RecompensaEstudiante).filter(
        RecompensaEstudiante.estudiante_id == asignacion.estudiante_id,
        RecompensaEstudiante.recompensa_id == asignacion.recompensa_id
    ).first()
    if existente:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El estudiante ya tiene esta recompensa"
        )
    
    db_asignacion = RecompensaEstudiante(**asignacion.dict())
    db.add(db_asignacion)
    db.commit()
    db.refresh(db_asignacion)
    return db_asignacion

def obtener_recompensas_estudiante(db: Session, estudiante_id: int):
    return db.query(RecompensaEstudiante).filter(RecompensaEstudiante.estudiante_id == estudiante_id).all()

def crear_mision_diaria(db: Session, mision: MisionDiariaCreate):
    db_mision = MisionDiaria(**mision.dict())
    db.add(db_mision)
    db.commit()
    db.refresh(db_mision)
    return db_mision

def obtener_misiones_estudiante(db: Session, estudiante_id: int, fecha: Optional[str] = None):
    query = db.query(MisionDiaria).filter(MisionDiaria.estudiante_id == estudiante_id)
    if fecha:
        query = query.filter(MisionDiaria.fecha == fecha)
    return query.all()

def actualizar_progreso_mision(db: Session, mision_id: int, progreso: int):
    db_mision = db.query(MisionDiaria).filter(MisionDiaria.id == mision_id).first()
    if not db_mision:
        raise HTTPException(status_code=404, detail="Misión no encontrada")
    
    db_mision.progreso = progreso
    if progreso >= db_mision.objetivo:
        db_mision.completada = True
    
    db.commit()
    db.refresh(db_mision)
    return db_mision

def agregar_puntos_estudiante(db: Session, puntos: HistorialPuntosCreate):
    """
    Agrega puntos a un estudiante y actualiza su nivel automáticamente.

    Esta es la ÚNICA función para agregar puntos - centraliza toda la lógica
    de gamificación de puntos y niveles.

    Validaciones:
    - El estudiante debe existir
    - Los puntos deben ser >= 0 (usa puntos negativos solo para penalizaciones explícitas)
    - Crea NivelEstudiante automáticamente si no existe

    Maneja automáticamente:
    - Incremento de puntos totales
    - Incremento de XP del nivel actual
    - Subida de nivel cuando se alcanza el umbral
    - Registro en historial_puntos
    """

    # ============================================
    # 1. VALIDACIONES
    # ============================================

    # Validar que el estudiante existe
    estudiante = db.query(Estudiante).filter(
        Estudiante.id == puntos.estudiante_id
    ).first()

    if not estudiante:
        logger.error(f"❌ Intento de agregar puntos a estudiante inexistente ID={puntos.estudiante_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Estudiante con ID {puntos.estudiante_id} no encontrado"
        )

    # Validar puntos no negativos (a menos que sea penalización explícita)
    if puntos.puntos < 0:
        logger.warning(f"⚠️ Agregando puntos negativos ({puntos.puntos}) a estudiante {estudiante.nombre} - Motivo: {puntos.motivo}")

    # ============================================
    # 2. REGISTRAR PUNTOS EN HISTORIAL
    # ============================================

    db_puntos = HistorialPuntos(**puntos.dict())
    db.add(db_puntos)
    db.flush()  # Para obtener el ID sin hacer commit aún

    logger.info(f"📊 Puntos registrados: +{puntos.puntos} para {estudiante.nombre} - Motivo: {puntos.motivo}")

    # ============================================
    # 3. OBTENER O CREAR NIVEL DEL ESTUDIANTE
    # ============================================

    nivel_estudiante = db.query(NivelEstudiante).filter(
        NivelEstudiante.estudiante_id == puntos.estudiante_id
    ).first()

    if not nivel_estudiante:
        # Crear registro de nivel si no existe
        nivel_estudiante = NivelEstudiante(
            estudiante_id=puntos.estudiante_id,
            nivel_actual=1,
            puntos_totales=0,
            puntos_nivel_actual=0,
            puntos_para_siguiente_nivel=1000,
            lecturas_completadas=0,
            actividades_completadas=0,
            racha_actual=0,
            racha_maxima=0
        )
        db.add(nivel_estudiante)
        db.flush()
        logger.info(f"✨ Nivel inicial creado para estudiante {estudiante.nombre}")

    # ============================================
    # 4. ACTUALIZAR PUNTOS Y NIVEL
    # ============================================

    nivel_anterior = nivel_estudiante.nivel_actual

    # Actualizar puntos
    nivel_estudiante.puntos_totales += puntos.puntos
    nivel_estudiante.puntos_nivel_actual += puntos.puntos

    # ============================================
    # 5. LÓGICA DE SUBIDA DE NIVEL
    # ============================================

    # Verificar si subió de nivel (puede subir múltiples niveles si ganó muchos puntos)
    niveles_subidos = 0
    while nivel_estudiante.puntos_nivel_actual >= nivel_estudiante.puntos_para_siguiente_nivel:
        # Restar los puntos necesarios para el nivel
        nivel_estudiante.puntos_nivel_actual -= nivel_estudiante.puntos_para_siguiente_nivel

        # Subir de nivel
        nivel_estudiante.nivel_actual += 1
        niveles_subidos += 1

        # Calcular puntos necesarios para el siguiente nivel
        # Fórmula: nivel * 1000 (cada nivel requiere más puntos)
        nivel_estudiante.puntos_para_siguiente_nivel = nivel_estudiante.nivel_actual * 1000

        logger.info(f"🎉 ¡{estudiante.nombre} subió al nivel {nivel_estudiante.nivel_actual}!")

    # Log si NO subió de nivel pero ganó puntos
    if niveles_subidos == 0 and puntos.puntos > 0:
        puntos_faltantes = nivel_estudiante.puntos_para_siguiente_nivel - nivel_estudiante.puntos_nivel_actual
        logger.debug(
            f"📈 {estudiante.nombre}: {nivel_estudiante.puntos_nivel_actual}/{nivel_estudiante.puntos_para_siguiente_nivel} XP "
            f"(faltan {puntos_faltantes} para nivel {nivel_estudiante.nivel_actual + 1})"
        )

    # ============================================
    # 6. COMMIT Y RETORNO
    # ============================================

    try:
        db.commit()
        db.refresh(db_puntos)

        # Log final
        if niveles_subidos > 0:
            logger.info(
                f"✅ Puntos agregados exitosamente: {estudiante.nombre} "
                f"({nivel_anterior} → {nivel_estudiante.nivel_actual}, +{puntos.puntos} pts)"
            )
        else:
            logger.info(
                f"✅ Puntos agregados exitosamente: {estudiante.nombre} "
                f"(Nivel {nivel_estudiante.nivel_actual}, +{puntos.puntos} pts)"
            )

        return db_puntos

    except Exception as e:
        db.rollback()
        logger.error(f"❌ Error al agregar puntos: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al procesar puntos: {str(e)}"
        )

def obtener_historial_puntos_estudiante(db: Session, estudiante_id: int, skip: int = 0, limit: int = 50):
    return db.query(HistorialPuntos).filter(
        HistorialPuntos.estudiante_id == estudiante_id
    ).offset(skip).limit(limit).all()