import logging
import sys


# ANSI Color Codes
class Colors:
    HEADER = "\033[95m"
    INFO = "\033[94m"
    SUCCESS = "\033[92m"
    WARNING = "\033[93m"
    ERROR = "\033[91m"
    RESET = "\033[0m"
    BOLD = "\033[1m"


class ColoredFormatter(logging.Formatter):
    """Custom formatter that adds colors to log messages"""

    FORMATS = {
        logging.DEBUG: Colors.HEADER
        + "%(asctime)s - %(levelname)s - %(message)s"
        + Colors.RESET,
        logging.INFO: Colors.INFO
        + "%(asctime)s - %(levelname)s - %(message)s"
        + Colors.RESET,
        logging.WARNING: Colors.WARNING
        + "%(asctime)s - %(levelname)s - %(message)s"
        + Colors.RESET,
        logging.ERROR: Colors.ERROR
        + "%(asctime)s - %(levelname)s - %(message)s"
        + Colors.RESET,
        logging.CRITICAL: Colors.ERROR
        + Colors.BOLD
        + "%(asctime)s - %(levelname)s - %(message)s"
        + Colors.RESET,
    }

    def format(self, record):
        log_format = self.FORMATS.get(record.levelno)
        formatter = logging.Formatter(log_format, datefmt="%Y-%m-%d %H:%M:%S")
        return formatter.format(record)


def setup_logger(name: str = "discord_bot") -> logging.Logger:
    """
    Set up and return a logger instance with colored output

    Args:
        name (str): Name of the logger instance

    Returns:
        logging.Logger: Configured logger instance
    """
    logger = logging.getLogger(name)

    if not logger.handlers:  # Prevent adding handlers multiple times
        logger.setLevel(logging.INFO)

        # Create console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(ColoredFormatter())

        logger.addHandler(console_handler)

    return logger


# Create default logger instance
logger = setup_logger()


# Convenience methods
def info(msg: str) -> None:
    logger.info(msg)


def warning(msg: str) -> None:
    logger.warning(msg)


def error(msg: str) -> None:
    logger.error(msg)


def critical(msg: str) -> None:
    logger.critical(msg)


def debug(msg: str) -> None:
    logger.debug(msg)
