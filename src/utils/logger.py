from colorama import Fore, Style, init
from datetime import datetime
import logging
import os

# Initialize colorama for cross-platform colored output
init(autoreset=True)


class CustomFormatter(logging.Formatter):
    """Custom formatter with colors and better formatting"""

    FORMATS = {
        logging.DEBUG: Fore.MAGENTA
        + "[{asctime}] [🔍 DEBUG] {message}"
        + Style.RESET_ALL,
        logging.INFO: Fore.CYAN + "[{asctime}] [ℹ️ INFO] {message}" + Style.RESET_ALL,
        logging.WARNING: Fore.YELLOW
        + "[{asctime}] [⚠️ WARNING] {message}"
        + Style.RESET_ALL,
        logging.ERROR: Fore.RED + "[{asctime}] [❌ ERROR] {message}" + Style.RESET_ALL,
        logging.CRITICAL: Fore.RED
        + Style.BRIGHT
        + "[{asctime}] [☠️ CRITICAL] {message}"
        + Style.RESET_ALL,
    }

    def format(self, record):
        # Save the original format
        format_orig = self._style._fmt

        # Replace the original format with our custom format
        self._style._fmt = self.FORMATS.get(record.levelno, format_orig)

        # Format the record
        result = super().format(record)

        # Restore the original format
        self._style._fmt = format_orig

        return result


class Logger:
    def __init__(self):
        self.log_directory = "logs"
        self.log_file = "bot.log"
        self.logger = logging.getLogger("discord_bot")
        self.setup_logger()

    def setup_logger(self):
        """Set up the logger with custom formatting and handlers"""
        self.ensure_log_directory()
        self.logger.setLevel(logging.DEBUG)

        # Prevent duplicate handlers
        if self.logger.handlers:
            return

        # Console Handler
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(
            CustomFormatter(style="{", datefmt="%Y-%m-%d %H:%M:%S")
        )

        # File Handler - Using 'w' mode to overwrite the file on each run
        file_handler = logging.FileHandler(
            os.path.join(self.log_directory, self.log_file),
            mode="w",  # This will overwrite the file on each run
            encoding="utf-8",
        )
        file_handler.setFormatter(
            logging.Formatter(
                "[{asctime}] [{levelname}] {message}",
                style="{",
                datefmt="%Y-%m-%d %H:%M:%S",
            )
        )

        self.logger.addHandler(console_handler)
        self.logger.addHandler(file_handler)

    def ensure_log_directory(self):
        """Create logs directory if it doesn't exist"""
        if not os.path.exists(self.log_directory):
            os.makedirs(self.log_directory)

    def debug(self, message: str):
        self.logger.debug(message)

    def info(self, message: str):
        self.logger.info(message)

    def warning(self, message: str):
        self.logger.warning(message)

    def error(self, message: str):
        self.logger.error(message)

    def critical(self, message: str):
        self.logger.critical(message)


# Create a global logger instance
logger = Logger()

# Export the logger's methods directly
debug = logger.debug
info = logger.info
warning = logger.warning
error = logger.error
critical = logger.critical
