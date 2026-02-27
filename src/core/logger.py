import logging
import sys
from typing import Literal

# Definición de tipos para los niveles permitidos
LogLevel = Literal["DEBUG", "INFO", "WARNING", "ERROR"]

class InfoFilter(logging.Filter):
    """Filtro para permitir solo niveles INFO y DEBUG en stdout."""
    def filter(self, record: logging.LogRecord) -> bool:
        return record.levelno <= logging.INFO

def setup_logger(level: LogLevel = "INFO") -> logging.Logger:
    """Configura y devuelve el logger principal del proyecto."""
    logger = logging.getLogger("bethurtadom")
    
    # Evitar duplicados si se llama varias veces
    if logger.hasHandlers():
        logger.handlers.clear()

    # Mapeo de niveles
    level_map = {
        "DEBUG": logging.DEBUG,
        "INFO": logging.INFO,
        "WARNING": logging.WARNING,
        "ERROR": logging.ERROR
    }
    
    logger.setLevel(level_map.get(level, logging.INFO))

    # Formato del mensaje: [NIVEL] Mensaje
    formatter = logging.Formatter("[%(levelname)s] %(message)s")

    # Handler para STDOUT (ALL y USER)
    stdout_handler = logging.StreamHandler(sys.stdout)
    stdout_handler.setFormatter(formatter)
    stdout_handler.addFilter(InfoFilter())
    logger.addHandler(stdout_handler)

    # Handler para STDERR (WARNING y ERROR)
    stderr_handler = logging.StreamHandler(sys.stderr)
    stderr_handler.setFormatter(formatter)
    stderr_handler.setLevel(logging.WARNING)
    logger.addHandler(stderr_handler)

    return logger

# Instancia global por defecto
logger = setup_logger()
