import logging
import sys
from colorama import init, Fore, Style

init(autoreset=True)


class ColoredFormatter(logging.Formatter):
    """A formatter that adds color to log messages."""

    FORMAT = "%(asctime)s - %(levelname)s - %(message)s"

    FORMATS = {
        logging.DEBUG: Fore.CYAN + FORMAT + Style.RESET_ALL,
        logging.INFO: Fore.GREEN + FORMAT + Style.RESET_ALL,
        logging.WARNING: Fore.YELLOW + FORMAT + Style.RESET_ALL,
        logging.ERROR: Fore.RED + FORMAT + Style.RESET_ALL,
        logging.CRITICAL: Fore.RED + Style.BRIGHT + FORMAT + Style.RESET_ALL,
    }

    def format(self, record):
        log_fmt = self.FORMATS.get(record.levelno)
        formatter = logging.Formatter(log_fmt, datefmt="%Y-%m-%d %H:%M:%S")
        return formatter.format(record)


def setup_logger(log_level: str = "INFO") -> logging.Logger:
    """Sets up the logger with colored output and specified log level."""
    level = getattr(logging, log_level.upper(), logging.INFO)
    logger = logging.getLogger("eidos")
    logger.setLevel(level)

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(ColoredFormatter())
    logger.addHandler(handler)

    return logger


logger = setup_logger()
