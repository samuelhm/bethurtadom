import logging
import sys
from typing import Literal

# Definición de tipos para los niveles estándar
LogLevel = Literal["DEBUG", "INFO", "WARNING", "ERROR"]


class ColorFormatter(logging.Formatter):
    """Formatter personalizado para añadir colores a los logs en consola."""

    # Códigos ANSI para colores
    GREY = "\x1b[38;20m"  # Blanco/Gris para DEBUG
    GREEN = "\x1b[32;20m"  # Verde para INFO
    YELLOW = "\x1b[33;20m"  # Amarillo para WARNING
    RED = "\x1b[31;20m"  # Rojo para ERROR
    BOLD_RED = "\x1b[31;1m"  # Rojo negrita para CRITICAL
    RESET = "\x1b[0m"  # Reset de color

    FORMAT = "[%(levelname)s] %(message)s"

    LEVEL_COLORS = {
        logging.DEBUG: GREY,
        logging.INFO: GREEN,
        logging.WARNING: YELLOW,
        logging.ERROR: RED,
        logging.CRITICAL: BOLD_RED,
    }

    def format(self, record: logging.LogRecord) -> str:
        log_color = self.LEVEL_COLORS.get(record.levelno, self.RESET)
        format_str = f"{log_color}{self.FORMAT}{self.RESET}"
        formatter = logging.Formatter(format_str)
        return formatter.format(record)


class InfoFilter(logging.Filter):
    """Filtro para permitir solo niveles INFO y DEBUG en stdout."""

    def filter(self, record: logging.LogRecord) -> bool:
        return record.levelno <= logging.INFO


def setup_logger(level: LogLevel = "INFO") -> logging.Logger:
    """Configura y devuelve el logger principal con nombres estándar y colores."""
    logger = logging.getLogger("bethurtadom")

    if logger.hasHandlers():
        logger.handlers.clear()

    # Mapeo directo a constantes de logging
    level_map = {
        "DEBUG": logging.DEBUG,
        "INFO": logging.INFO,
        "WARNING": logging.WARNING,
        "ERROR": logging.ERROR,
    }

    logger.setLevel(level_map.get(level, logging.INFO))
    formatter = ColorFormatter()

    # Handler para STDOUT (DEBUG e INFO)
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
logger = setup_logger("DEBUG")
