# app/routers/padres.py

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Optional
from pydantic import BaseModel, EmailStr
from passlib.context import CryptContext

from app.config import get_db
from app.modelos import Estudiante, Padre, ContenidoLectura, Actividad, Usuario, EvaluacionLectura
from app.servicios.seguridad import obtener_usuario_actual

from app.servicios.padre_hijos import obtener_hijos_con_cursos
from app.esquemas.padre_hijos import EstudianteConCursosResponse

from app.esquemas.padre import PadreResponse, PadreCreate, PadreUpdate, VincularHijoRequest
from app.servicios.padre import crear_padre, obtener_padres, obtener_padre as obtener_padre_service

from app.servicios.estudiante import obtener_cursos_estudiante

# Configurar bcrypt para contraseñas
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

router = APIRouter(prefix="/padres", tags=["Padres"])


# ============================================================
# SCHEMAS PARA EDITAR PERFIL
# ============================================================

class PadrePerfilResponse(BaseModel):
    """Schema para retornar datos del perfil del padre"""
    id: int
    nombre: str
    apellido: str
    email: str
    telefono_contacto: Optional[str] = None
    parentesco: Optional[str] = None
    notificaciones_activas: bool = True
    
    class Config:
        from_attributes = True


class ActualizarPerfilRequest(BaseModel):
    """Schema para actualizar perfil del padre"""
    nombre: str
    apellido: str
    email: EmailStr
    telefono_contacto: Optional[str] = None
    password_actual: Optional[str] = None  # Opcional - solo si quiere cambiar password
    password: Optional[str] = None  # Nueva contraseña


# ============================================================
# 1. LISTAR HIJOS DEL PADRE (MEJORADO - SOLO ACTIVOS)
# ============================================================
@router.get("/mis-hijos")
def listar_hijos_con_cursos(
    db: Session = Depends(get_db),
    usuario_actual: Usuario = Depends(obtener_usuario_actual)
):
    """
    Obtiene la lista de hijos vinculados al padre actual.
    Solo retorna estudiantes activos.
    """
    padre = db.query(Padre).filter(Padre.usuario_id == usuario_actual.id).first()
    
    if not padre:
        raise HTTPException(status_code=404, detail="No se encontró el perfil de padre")
    
    # Obtener solo hijos activos vinculados a este padre
    estudiantes = (
        db.query(Estudiante)
        .filter(
            Estudiante.padre_id == padre.id,
            Estudiante.activo == True
        )
        .all()
    )
    
    # Construir respuesta
    result = []
    for estudiante in estudiantes:
        cursos = obtener_cursos_estudiante(db, estudiante.id)
        
        # Obtener info del docente
        docente_info = None
        if estudiante.docente:
            if estudiante.docente.usuario:
                docente_info = {
                    "id": estudiante.docente.id,
                    "nombre": estudiante.docente.usuario.nombre,
                    "apellido": estudiante.docente.usuario.apellido
                }
        
        estudiante_data = {
            "id": estudiante.id,
            "nombre": estudiante.nombre,
            "apellido": estudiante.apellido,
            "fecha_nacimiento": str(estudiante.fecha_nacimiento),
            "nivel_educativo": estudiante.nivel_educativo,
            "activo": estudiante.activo,
            "avatar_url": estudiante.avatar_url,
            "docente": docente_info,
            "cursos": [
                {
                    "id": curso.id,
                    "nombre": curso.nombre,
                    "descripcion": curso.descripcion,
                    "grado": getattr(curso, 'grado', None)
                }
                for curso in cursos
            ]
        }
        result.append(estudiante_data)
    
    return result


# ============================================================
# 2. CRUD PADRES (POST y GET lista)
# ============================================================
@router.post("/", response_model=PadreResponse)
def crear_padre_route(padre: PadreCreate, db: Session = Depends(get_db)):
    return crear_padre(db, padre)


@router.get("/", response_model=List[PadreResponse])
def listar_padres_route(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return obtener_padres(db, skip, limit)


# ============================================================
# 3. 🔥 MI-PERFIL (DEBE IR ANTES DE /{padre_id})
# ============================================================

@router.get("/mi-perfil-debug")
def obtener_mi_perfil_debug(
    db: Session = Depends(get_db),
    usuario_actual: Usuario = Depends(obtener_usuario_actual)
):
    """DEBUG: Ver datos sin validación"""
    try:
        padre = db.query(Padre).filter(
            Padre.usuario_id == usuario_actual.id
        ).first()
        
        if not padre:
            return {
                "status": "NO_PADRE",
                "usuario_id": usuario_actual.id,
                "email": usuario_actual.email
            }
        
        return {
            "status": "OK",
            "datos": {
                "padre_id": padre.id,
                "nombre": usuario_actual.nombre,
                "apellido": usuario_actual.apellido,
                "email": usuario_actual.email,
                "telefono": padre.telefono_contacto,
                "parentesco": padre.parentesco,
                "notificaciones": padre.notificaciones_activas,
                "padre_activo": padre.activo
            }
        }
    except Exception as e:
        return {"status": "ERROR", "error": str(e)}


@router.get("/mi-perfil", response_model=PadrePerfilResponse)
def obtener_mi_perfil(
    db: Session = Depends(get_db),
    usuario_actual: Usuario = Depends(obtener_usuario_actual)
):
    """
    Obtiene el perfil completo del padre autenticado.
    Retorna datos del Usuario y del Padre.
    """
    
    # Buscar el padre asociado al usuario actual
    padre = db.query(Padre).filter(
        Padre.usuario_id == usuario_actual.id,
        Padre.activo == True
    ).first()
    
    if not padre:
        raise HTTPException(
            status_code=404,
            detail="No se encontró el perfil de padre para este usuario."
        )
    
    # Construir respuesta con datos de Usuario y Padre
    return {
        "id": padre.id,
        "nombre": usuario_actual.nombre,
        "apellido": usuario_actual.apellido,
        "email": usuario_actual.email,
        "telefono_contacto": padre.telefono_contacto,
        "parentesco": padre.parentesco,
        "notificaciones_activas": padre.notificaciones_activas
    }


@router.put("/mi-perfil", response_model=PadrePerfilResponse)
def actualizar_mi_perfil(
    datos: ActualizarPerfilRequest,
    db: Session = Depends(get_db),
    usuario_actual: Usuario = Depends(obtener_usuario_actual)
):
    """
    Actualiza el perfil del padre autenticado.
    Permite actualizar:
    - Nombre, apellido, email (en tabla Usuario)
    - Teléfono de contacto (en tabla Padre)
    - Contraseña (opcional - solo si proporciona password_actual)
    """
    
    # 1. Buscar el padre asociado al usuario actual
    padre = db.query(Padre).filter(
        Padre.usuario_id == usuario_actual.id,
        Padre.activo == True
    ).first()
    
    if not padre:
        raise HTTPException(
            status_code=404,
            detail="No se encontró el perfil de padre."
        )
    
    # 2. Buscar el usuario en la base de datos
    usuario = db.query(Usuario).filter(Usuario.id == usuario_actual.id).first()
    
    if not usuario:
        raise HTTPException(
            status_code=404,
            detail="No se encontró el usuario."
        )
    
    # 3. VALIDAR EMAIL ÚNICO (si cambió)
    if datos.email != usuario.email:
        email_existente = db.query(Usuario).filter(
            Usuario.email == datos.email,
            Usuario.id != usuario.id
        ).first()
        
        if email_existente:
            raise HTTPException(
                status_code=400,
                detail="El email ya está en uso por otro usuario."
            )
    
    # 4. CAMBIAR CONTRASEÑA (si se proporcionó)
    if datos.password_actual and datos.password:
        # Verificar contraseña actual
        if not pwd_context.verify(datos.password_actual, usuario.password_hash):
            raise HTTPException(
                status_code=400,
                detail="La contraseña actual es incorrecta."
            )
        
        # Validar longitud de nueva contraseña
        if len(datos.password) < 6:
            raise HTTPException(
                status_code=400,
                detail="La nueva contraseña debe tener al menos 6 caracteres."
            )
        
        # Hashear y actualizar contraseña
        usuario.password_hash = pwd_context.hash(datos.password)
    
    # 5. ACTUALIZAR DATOS EN TABLA USUARIO
    usuario.nombre = datos.nombre
    usuario.apellido = datos.apellido
    usuario.email = datos.email
    usuario.fecha_actualizacion = func.now()
    
    # 6. ACTUALIZAR DATOS EN TABLA PADRE
    if datos.telefono_contacto is not None:
        padre.telefono_contacto = datos.telefono_contacto
    
    # 7. GUARDAR CAMBIOS
    try:
        db.commit()
        db.refresh(usuario)
        db.refresh(padre)
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Error al guardar los cambios: {str(e)}"
        )
    
    # 8. RETORNAR DATOS ACTUALIZADOS
    return {
        "id": padre.id,
        "nombre": usuario.nombre,
        "apellido": usuario.apellido,
        "email": usuario.email,
        "telefono_contacto": padre.telefono_contacto,
        "parentesco": padre.parentesco,
        "notificaciones_activas": padre.notificaciones_activas
    }


# ============================================================
# 4. OBTENER PADRE POR ID (DEBE IR DESPUÉS DE /mi-perfil)
# ============================================================
@router.get("/{padre_id}", response_model=PadreResponse)
def obtener_padre_route(padre_id: int, db: Session = Depends(get_db)):
    db_padre = obtener_padre_service(db, padre_id)
    if not db_padre:
        raise HTTPException(404, "Padre no encontrado")
    return db_padre


# ============================================================
# 5. VINCULAR HIJO (MEJORADO CON REACTIVACIÓN)
# ============================================================
@router.post("/vincular-hijo", response_model=dict)
def vincular_hijo(
    data: VincularHijoRequest,
    db: Session = Depends(get_db),
    usuario_actual = Depends(obtener_usuario_actual)
):
    """
    Vincula un hijo al padre actual usando nombre, apellido y fecha de nacimiento.
    Si el estudiante ya estaba vinculado pero inactivo, lo reactiva.
    """
    padre = db.query(Padre).filter(Padre.usuario_id == usuario_actual.id).first()

    if not padre:
        raise HTTPException(status_code=400, detail="No existe registro de padre.")

    # Buscar estudiante por nombre, apellido y fecha de nacimiento
    estudiante = (
        db.query(Estudiante)
        .filter(
            Estudiante.nombre.ilike(data.nombre),
            Estudiante.apellido.ilike(data.apellido),
            Estudiante.fecha_nacimiento == data.fecha_nacimiento,
        )
        .first()
    )

    if not estudiante:
        raise HTTPException(
            status_code=404, 
            detail="No se encontró un estudiante con esos datos. Verifica con el docente."
        )

    # ✅ Verificar si ya está vinculado a este padre
    if estudiante.padre_id == padre.id:
        if estudiante.activo:
            raise HTTPException(
                status_code=400, 
                detail="Este hijo ya está vinculado a tu cuenta."
            )
        else:
            # REACTIVAR si estaba inactivo
            estudiante.activo = True
            estudiante.deleted_at = None
            db.commit()
            db.refresh(estudiante)
            return {"mensaje": "Hijo revinculado exitosamente. ¡Bienvenido de vuelta! 🎉"}
    
    # ✅ Verificar si está vinculado a otro padre
    if estudiante.padre_id is not None and estudiante.padre_id != padre.id:
        raise HTTPException(
            status_code=400, 
            detail="Este estudiante ya tiene un padre asignado."
        )

    # ✅ VINCULAR por primera vez
    estudiante.padre_id = padre.id
    estudiante.activo = True
    estudiante.deleted_at = None
    db.commit()
    db.refresh(estudiante)

    return {"mensaje": "Hijo vinculado correctamente. ¡Éxito! 🎉"}


# ============================================================
# 6. DESVINCULAR HIJO (SOFT DELETE)
# ============================================================
@router.delete("/desvincular-hijo/{estudiante_id}", response_model=dict)
def desvincular_hijo(
    estudiante_id: int,
    db: Session = Depends(get_db),
    usuario_actual: Usuario = Depends(obtener_usuario_actual)
):
    """
    Desvincula un hijo del padre actual (soft delete).
    El estudiante se marca como inactivo pero no se elimina.
    """
    
    padre = db.query(Padre).filter(Padre.usuario_id == usuario_actual.id).first()
    
    if not padre:
        raise HTTPException(
            status_code=404, 
            detail="No se encontró el perfil de padre."
        )
    
    # Buscar el estudiante
    estudiante = (
        db.query(Estudiante)
        .filter(
            Estudiante.id == estudiante_id,
            Estudiante.padre_id == padre.id,
            Estudiante.activo == True
        )
        .first()
    )
    
    if not estudiante:
        raise HTTPException(
            status_code=404,
            detail="No se encontró el hijo o ya fue desvinculado."
        )
    
    # ✅ SOFT DELETE
    estudiante.activo = False
    estudiante.deleted_at = func.now()
    db.commit()
    db.refresh(estudiante)
    
    return {
        "mensaje": "Hijo desvinculado exitosamente.",
        "estudiante_id": estudiante.id,
        "nombre_completo": f"{estudiante.nombre} {estudiante.apellido}",
        "nota": "El estudiante fue marcado como inactivo. Puedes revincularlo en cualquier momento."
    }


# ============================================================
# 7. LECTURAS DEL HIJO (ACTUALIZADO CON CAMPO COMPLETADA)
# ============================================================
@router.get("/hijos/{hijo_id}/lecturas")
def obtener_lecturas_hijo(
    hijo_id: int,
    db: Session = Depends(get_db),
    usuario_actual: Usuario = Depends(obtener_usuario_actual)
):
    """
    Obtiene las lecturas y actividades disponibles para un hijo específico.
    ✅ ACTUALIZADO: Marca como completadas las lecturas que tienen evaluación.
    """
    padre = db.query(Padre).filter(Padre.usuario_id == usuario_actual.id).first()
    
    if not padre:
        raise HTTPException(
            status_code=403, 
            detail="No existe registro de padre para este usuario."
        )

    estudiante = db.query(Estudiante).filter(Estudiante.id == hijo_id).first()
    
    if not estudiante:
        raise HTTPException(status_code=404, detail="El estudiante no existe.")

    # ✅ Validar que sea hijo del padre actual
    if estudiante.padre_id != padre.id:
        raise HTTPException(
            status_code=403, 
            detail="No tienes permiso para ver las lecturas de este estudiante."
        )
    
    # ✅ Validar que el hijo esté activo
    if not estudiante.activo:
        raise HTTPException(
            status_code=403,
            detail="Este hijo está desvinculado. Revíncúlalo para ver sus lecturas."
        )

    # 🔥 OBTENER EVALUACIONES DEL ESTUDIANTE CON UMBRAL DE APROBACIÓN
    # Solo se consideran completadas las lecturas con precision_palabras >= 70%
    UMBRAL_APROBACION = 70.0  # Puedes cambiar este valor (60, 70, 80, etc.)
    
    evaluaciones = (
        db.query(EvaluacionLectura.contenido_id)
        .filter(
            EvaluacionLectura.estudiante_id == hijo_id,
            EvaluacionLectura.precision_palabras.isnot(None),  # ✅ EXCLUIR NULL
            EvaluacionLectura.precision_palabras >= UMBRAL_APROBACION  # ✅ VALIDACIÓN DE UMBRAL
        )
        .distinct()
        .all()
    )
    
    # Crear set de IDs de lecturas completadas (solo las que superaron el umbral)
    lecturas_completadas_ids = {ev.contenido_id for ev in evaluaciones}

    cursos = obtener_cursos_estudiante(db, hijo_id)
    
    if not cursos:
        return []

    lecturas_finales = []

    for curso in cursos:
        lecturas = (
            db.query(ContenidoLectura)
            .filter(
                ContenidoLectura.curso_id == curso.id,
                ContenidoLectura.activo == True
            )
            .all()
        )

        for lectura in lecturas:
            actividades = (
                db.query(Actividad)
                .filter(
                    Actividad.contenido_id == lectura.id,
                    Actividad.activo == True
                )
                .all()
            )

            # 🔥 OBTENER EL MEJOR PUNTAJE DE LA LECTURA (si la practicó)
            mejor_evaluacion = (
                db.query(EvaluacionLectura)
                .filter(
                    EvaluacionLectura.estudiante_id == hijo_id,
                    EvaluacionLectura.contenido_id == lectura.id,
                    EvaluacionLectura.precision_palabras.isnot(None)  # ✅ EXCLUIR NULL
                )
                .order_by(EvaluacionLectura.precision_palabras.desc())
                .first()
            )
            
            mejor_puntaje = mejor_evaluacion.precision_palabras if mejor_evaluacion else None
            esta_completada = lectura.id in lecturas_completadas_ids
            
            # 🔥 AGREGAR CAMPO COMPLETADA Y PUNTAJE
            lecturas_finales.append(
                {
                    "id": lectura.id,
                    "titulo": lectura.titulo,
                    "contenido": lectura.contenido,
                    "curso": curso.nombre,
                    "nivel_dificultad": lectura.nivel_dificultad,
                    "edad_recomendada": lectura.edad_recomendada,
                    "completada": esta_completada,  # ✅ Solo true si puntaje >= 70
                    "mejor_puntaje": mejor_puntaje,  # ✅ NUEVO: Muestra el mejor puntaje obtenido
                    "umbral_aprobacion": UMBRAL_APROBACION,  # ✅ NUEVO: Para mostrar en frontend
                    "actividades": [
                        {
                            "id": act.id,
                            "tipo": act.tipo,
                            "titulo": act.titulo,
                            "descripcion": getattr(act, 'descripcion', ''),
                            "puntos_maximos": act.puntos_maximos,
                            "tiempo_estimado": getattr(act, 'tiempo_estimado', None),
                            "dificultad": getattr(act, 'dificultad', None),
                        }
                        for act in actividades
                    ],
                }
            )

    return lecturas_finales


# ============================================================
# 8. OBTENER PROGRESO DEL HIJO
# ============================================================
@router.get("/hijo/{estudiante_id}/progreso")
def obtener_progreso_hijo(
    estudiante_id: int,
    db: Session = Depends(get_db),
    usuario_actual: Usuario = Depends(obtener_usuario_actual)
):
    """
    Obtiene estadísticas y progreso académico de un hijo específico.
    """
    
    padre = db.query(Padre).filter(Padre.usuario_id == usuario_actual.id).first()
    
    if not padre:
        raise HTTPException(
            status_code=404, 
            detail="No se encontró el perfil de padre."
        )
    
    # Verificar que el estudiante esté vinculado y activo
    estudiante = (
        db.query(Estudiante)
        .filter(
            Estudiante.id == estudiante_id,
            Estudiante.padre_id == padre.id,
            Estudiante.activo == True
        )
        .first()
    )
    
    if not estudiante:
        raise HTTPException(
            status_code=403,
            detail="No tienes permiso para ver el progreso de este estudiante o está desvinculado."
        )
    
    # TODO: Implementar lógica de progreso real
    
    return {
        "estudiante_id": estudiante.id,
        "nombre_completo": f"{estudiante.nombre} {estudiante.apellido}",
        "mensaje": "Módulo de progreso en desarrollo",
        "estadisticas": {
            "actividades_completadas": 0,
            "actividades_totales": 0,
            "puntaje_promedio": 0,
            "tiempo_total_minutos": 0
        }
    }
