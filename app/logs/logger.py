import logging
import os
from logging.handlers import RotatingFileHandler
import psycopg2
from psycopg2.extras import Json
from datetime import datetime
import traceback


BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOGS_DIR = os.path.join(BASE_DIR, "logs")

if not os.path.exists(LOGS_DIR):
    os.makedirs(LOGS_DIR)

log_file = os.path.join(LOGS_DIR, "app.log")


class PostgreSQLHandler(logging.Handler):
    """Handler para guardar logs en PostgreSQL"""
    
    def __init__(self, db_config):
        super().__init__()
        self.db_config = db_config
        self._connection_failed = False
        
    def get_connection(self):
        return psycopg2.connect(**self.db_config)
    
    def emit(self, record):
        if self._connection_failed:
            return
            
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
     
            ip_address = getattr(record, 'ip_address', None)
            endpoint = getattr(record, 'endpoint', None)
            method = getattr(record, 'method', None)
            status_code = getattr(record, 'status_code', None)
            user_id = getattr(record, 'user_id', None)
            
          
            extra_data = {
                'pathname': record.pathname,
                'thread': record.thread,
                'process': record.process,
            }
            
            if record.exc_info:
                extra_data['exception'] = ''.join(traceback.format_exception(*record.exc_info))
            
            cursor.execute("""
                INSERT INTO logs 
                (timestamp, level, logger_name, message, module, function, line_number, 
                 ip_address, endpoint, method, status_code, user_id, extra_data)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                datetime.fromtimestamp(record.created),
                record.levelname,
                record.name,
                record.getMessage(),
                record.module,
                record.funcName,
                record.lineno,
                ip_address,
                endpoint,
                method,
                status_code,
                user_id,
                Json(extra_data)
            ))
            
            conn.commit()
            cursor.close()
            conn.close()
            
        except Exception as e:
           
            self._connection_failed = True



DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'database': os.getenv('DB_NAME', 'proyecto_tutor'), 
    'user': os.getenv('DB_USER', 'postgres'),         
    'password': os.getenv('DB_PASSWORD', '12345'),  
    'port': int(os.getenv('DB_PORT', 5432))
}

logger = logging.getLogger("BookiSmartIA")
logger.setLevel(logging.INFO)

if not logger.handlers:
   
    file_handler = RotatingFileHandler(
        log_file,
        maxBytes=5_000_000,
        backupCount=5,
        encoding="utf-8",
    )

    formatter = logging.Formatter(
        "%(asctime)s - %(levelname)s - %(message)s"
    )
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    
 
    try:
        db_handler = PostgreSQLHandler(DB_CONFIG)
        db_handler.setLevel(logging.INFO)
        db_handler.setFormatter(formatter)
        logger.addHandler(db_handler)
    except:
        
        pass

logger.propagate = False