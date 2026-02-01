import logging
import os
from datetime import datetime

# Configuración simple para Azure
logger = logging.getLogger('BookiSmartIA')
logger.setLevel(logging.INFO)

# Solo usar StreamHandler para Azure (logs van a stdout/stderr)
if not logger.handlers:
    console_handler = logging.StreamHandler()
    formatter = logging.Formatter(
        '%(asctime)s - %(levelname)s - %(message)s'
    )
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

logger.propagate = False
