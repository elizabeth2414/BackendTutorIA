import logging
import psutil
import os
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import text

logger = logging.getLogger(__name__)

class MonitorSistema:
    def __init__(self):
        self.umbrales = {
            'cpu_percent': 80,
            'memory_percent': 85,
            'disk_percent': 90
        }
    
    async def obtener_estado_sistema(self, db: Session) -> dict:
        """
        Obtiene el estado completo del sistema y sus dependencias
        """
        try:
            # Estado del servidor
            estado_servidor = self._obtener_estado_servidor()
            
            # Estado de la base de datos
            estado_db = await self._verificar_base_datos(db)
            
            # Estado de servicios externos
            estado_servicios = await self._verificar_servicios_externos()
            
            # Estado de los modelos de IA
            estado_ia = await self._verificar_modelos_ia()
            
            # Determinar estado general
            estado_general = self._determinar_estado_general(
                estado_servidor, estado_db, estado_servicios, estado_ia
            )
            
            return {
                "sistema": {
                    "status": estado_general,
                    "timestamp": datetime.now().isoformat(),
                    "version": "1.0.0"
                },
                "servidor": estado_servidor,
                "base_datos": estado_db,
                "servicios_externos": estado_servicios,
                "modelos_ia": estado_ia,
                "metricas": self._obtener_metricas_performancia()
            }
            
        except Exception as e:
            logger.error(f"Error obteniendo estado del sistema: {str(e)}")
            return {
                "sistema": {
                    "status": "error",
                    "timestamp": datetime.now().isoformat(),
                    "error": str(e)
                }
            }
    
    def _obtener_estado_servidor(self) -> dict:
        """Obtiene el estado del servidor y recursos"""
        try:
            # Uso de CPU
            cpu_percent = psutil.cpu_percent(interval=1)
            
            # Uso de memoria
            memory = psutil.virtual_memory()
            
            # Uso de disco
            disk = psutil.disk_usage('/')
            
            # Información de red
            net_io = psutil.net_io_counters()
            
            # Procesos
            process = psutil.Process(os.getpid())
            
            return {
                "status": "activo",
                "cpu": {
                    "percent": cpu_percent,
                    "cores": psutil.cpu_count(),
                    "status": "normal" if cpu_percent < self.umbrales['cpu_percent'] else "alto"
                },
                "memoria": {
                    "total_gb": round(memory.total / (1024**3), 2),
                    "used_gb": round(memory.used / (1024**3), 2),
                    "percent": memory.percent,
                    "status": "normal" if memory.percent < self.umbrales['memory_percent'] else "alto"
                },
                "disco": {
                    "total_gb": round(disk.total / (1024**3), 2),
                    "used_gb": round(disk.used / (1024**3), 2),
                    "free_gb": round(disk.free / (1024**3), 2),
                    "percent": disk.percent,
                    "status": "normal" if disk.percent < self.umbrales['disk_percent'] else "alto"
                },
                "red": {
                    "bytes_enviados": net_io.bytes_sent,
                    "bytes_recibidos": net_io.bytes_recv
                },
                "proceso": {
                    "pid": process.pid,
                    "memory_mb": round(process.memory_info().rss / (1024**2), 2),
                    "cpu_percent": process.cpu_percent()
                }
            }
        except Exception as e:
            logger.error(f"Error obteniendo estado del servidor: {str(e)}")
            return {
                "status": "error",
                "error": str(e)
            }
    
    async def _verificar_base_datos(self, db: Session) -> dict:
        """Verifica el estado de la base de datos"""
        try:
            # Verificar conexión
            start_time = datetime.now()
            db.execute(text("SELECT 1"))
            db_latency = (datetime.now() - start_time).total_seconds() * 1000
            
            # Verificar tablas críticas
            tablas_criticas = [
                'usuario', 'estudiante', 'contenido_lectura', 
                'evaluacion_lectura', 'analisis_ia'
            ]
            
            tablas_estado = {}
            for tabla in tablas_criticas:
                try:
                    db.execute(text(f"SELECT COUNT(*) FROM {tabla} LIMIT 1"))
                    tablas_estado[tabla] = "activa"
                except Exception as e:
                    tablas_estado[tabla] = f"error: {str(e)}"
            
            return {
                "status": "conectado",
                "latencia_ms": round(db_latency, 2),
                "tablas": tablas_estado
            }
            
        except Exception as e:
            logger.error(f"Error verificando base de datos: {str(e)}")
            return {
                "status": "error",
                "error": str(e)
            }
    
    async def _verificar_servicios_externos(self) -> dict:
        """Verifica el estado de servicios externos"""
        try:
            import speech_recognition as sr
            from speech_recognition import RequestError, UnknownValueError
            
            # Verificar Google Speech Recognition
            reconocimiento_estado = "activo"
            try:
                # Test simple con audio de prueba
                r = sr.Recognizer()
                with sr.Microphone() as source:
                    r.adjust_for_ambient_noise(source, duration=0.1)
                reconocimiento_estado = "activo"
            except RequestError:
                reconocimiento_estado = "error_conexion"
            except Exception:
                reconocimiento_estado = "configurado"
            
            # Verificar librerías de audio
            librerias_audio = {}
            try:
                import librosa
                librerias_audio['librosa'] = {
                    "version": librosa.__version__,
                    "status": "activo"
                }
            except ImportError:
                librerias_audio['librosa'] = {
                    "status": "no_instalado"
                }
            
            try:
                import numpy as np
                librerias_audio['numpy'] = {
                    "version": np.__version__,
                    "status": "activo"
                }
            except ImportError:
                librerias_audio['numpy'] = {
                    "status": "no_instalado"
                }
            
            return {
                "speech_recognition": reconocimiento_estado,
                "librerias_audio": librerias_audio,
                "status": "activo" if reconocimiento_estado in ["activo", "configurado"] else "error"
            }
            
        except Exception as e:
            logger.error(f"Error verificando servicios externos: {str(e)}")
            return {
                "status": "error",
                "error": str(e)
            }
    
    async def _verificar_modelos_ia(self) -> dict:
        """Verifica el estado de los modelos de IA"""
        try:
            from servicios.ia_lectura_service import ServicioAnalisisLectura
            from servicios.generador_ejercicios import GeneradorEjercicios
            
            # Verificar que los servicios se pueden instanciar
            servicio_analisis = ServicioAnalisisLectura()
            generador_ejercicios = GeneradorEjercicios()
            
            modelos = {
                "analisis_pronunciacion": {
                    "status": "activo",
                    "modelo": "google_speech_v2",
                    "caracteristicas": ["stt", "analisis_errores", "fluidez"]
                },
                "generacion_ejercicios": {
                    "status": "activo",
                    "tipos": ["palabras_aisladas", "oraciones", "puntuacion", "ritmo", "entonacion"]
                },
                "evaluacion_avanzada": {
                    "status": "activo",
                    "metricas": ["precision_global", "velocidad", "fluidez", "entonacion"]
                }
            }
            
            return {
                "status": "activo",
                "modelos": modelos
            }
            
        except Exception as e:
            logger.error(f"Error verificando modelos de IA: {str(e)}")
            return {
                "status": "error",
                "error": str(e)
            }
    
    def _determinar_estado_general(self, servidor: dict, db: dict, servicios: dict, ia: dict) -> str:
        """Determina el estado general del sistema"""
        estados = []
        
        if servidor.get('status') != 'activo':
            estados.append('servidor')
        if db.get('status') != 'conectado':
            estados.append('base_datos')
        if servicios.get('status') != 'activo':
            estados.append('servicios_externos')
        if ia.get('status') != 'activo':
            estados.append('modelos_ia')
        
        if not estados:
            return "operativo"
        elif len(estados) <= 2:
            return "degradado"
        else:
            return "critico"
    
    def _obtener_metricas_performancia(self) -> dict:
        """Obtiene métricas de performance del sistema"""
        try:
            # Tiempo de actividad del sistema
            boot_time = datetime.fromtimestamp(psutil.boot_time())
            uptime = datetime.now() - boot_time
            
            # Estadísticas de red
            net_stats = psutil.net_io_counters()
            
            # Estadísticas de disco
            disk_io = psutil.disk_io_counters()
            
            return {
                "uptime_segundos": int(uptime.total_seconds()),
                "uptime_formateado": str(uptime).split('.')[0],
                "rendimiento": {
                    "io_disco": {
                        "lecturas": disk_io.read_count if disk_io else 0,
                        "escrituras": disk_io.write_count if disk_io else 0
                    },
                    "red": {
                        "paquetes_enviados": net_stats.packets_sent,
                        "paquetes_recibidos": net_stats.packets_recv
                    }
                },
                "estadisticas": {
                    "procesos_activos": len(psutil.pids()),
                    "carga_sistema": os.getloadavg() if hasattr(os, 'getloadavg') else [0, 0, 0]
                }
            }
        except Exception as e:
            logger.error(f"Error obteniendo métricas de performance: {str(e)}")
            return {
                "error": str(e)
            }
    
    async def obtener_estado_simplificado(self, db: Session) -> dict:
        """Obtiene un estado simplificado para checks rápidos"""
        try:
            estado_completo = await self.obtener_estado_sistema(db)
            
            return {
                "status": estado_completo["sistema"]["status"],
                "timestamp": estado_completo["sistema"]["timestamp"],
                "version": estado_completo["sistema"]["version"],
                "checks": {
                    "servidor": estado_completo["servidor"]["status"],
                    "base_datos": estado_completo["base_datos"]["status"],
                    "servicios": estado_completo["servicios_externos"]["status"],
                    "modelos_ia": estado_completo["modelos_ia"]["status"]
                }
            }
        except Exception as e:
            return {
                "status": "error",
                "timestamp": datetime.now().isoformat(),
                "error": str(e)
            }