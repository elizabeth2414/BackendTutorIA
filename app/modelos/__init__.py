# app/modelos/__init__.py

from app.config import Base

# Importar todos los modelos aquí para que estén disponibles
from app.modelos.usuario import Usuario
from app.modelos.contrasena_anterior import ContrasenaAnterior
from app.modelos.usuario_rol import UsuarioRol
from app.modelos.docente import Docente
from app.modelos.padre import Padre
from app.modelos.estudiante import Estudiante
from app.modelos.acceso_padre import AccesoPadre
from app.modelos.curso import Curso
from app.modelos.estudiante_curso import EstudianteCurso
from app.modelos.categoria_lectura import CategoriaLectura
from app.modelos.contenido_lectura import ContenidoLectura
from app.modelos.evaluacion_lectura import EvaluacionLectura
from app.modelos.analisis_ia import AnalisisIA
from app.modelos.intento_lectura import IntentoLectura
from app.modelos.detalle_evaluacion import DetalleEvaluacion
from app.modelos.error_pronunciacion import ErrorPronunciacion
from app.modelos.ejercicio_practica import EjercicioPractica
from app.modelos.resultado_ejercicio import ResultadoEjercicio
from app.modelos.audio_referencia import AudioReferencia
from app.modelos.fragmento_practica import FragmentoPractica
from app.modelos.actividad import Actividad
from app.modelos.pregunta import Pregunta
from app.modelos.progreso_actividad import ProgresoActividad
from app.modelos.respuesta_pregunta import RespuestaPregunta
from app.modelos.nivel_estudiante import NivelEstudiante
from app.modelos.recompensa import Recompensa
from app.modelos.recompensa_estudiante import RecompensaEstudiante
from app.modelos.mision_diaria import MisionDiaria
from app.modelos.historial_puntos import HistorialPuntos
from app.modelos.auditoria import Auditoria
from app.modelos.sesion_usuario import SesionUsuario
from .historial_pronunciacion import HistorialPronunciacion
from .historial_practica_pronunciacion import HistorialPracticaPronunciacion
from .historial_mejoras_ia import HistorialMejorasIA
from .actividad_lectura import ActividadLectura
from .password_reset_token import PasswordResetToken

__all__ = [
    "Base",
    "Usuario",
    "ContrasenaAnterior",
    "UsuarioRol",
    "Docente",
    "Padre",
    "Estudiante",
    "AccesoPadre",
    "Curso",
    "EstudianteCurso",
    "CategoriaLectura",
    "ContenidoLectura",
    "EvaluacionLectura",
    "AnalisisIA",
    "IntentoLectura",
    "DetalleEvaluacion",
    "ErrorPronunciacion",
    "EjercicioPractica",
    "ResultadoEjercicio",
    "AudioReferencia",
    "FragmentoPractica",
    "Actividad",
    "Pregunta",
    "ProgresoActividad",
    "RespuestaPregunta",
    "NivelEstudiante",
    "Recompensa",
    "RecompensaEstudiante",
    "MisionDiaria",
    "HistorialPuntos",
    "Auditoria",
    "SesionUsuario",
    "HistorialPronunciacion",
    "HistorialPracticaPronunciacion",
    "HistorialMejorasIA",
    "ActividadLectura",
    "PasswordResetToken",
]
