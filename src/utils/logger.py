from colorama import Fore, Style, init
from datetime import datetime
import os

# Initialize colorama for cross-platform colored output
init(autoreset=True)


class Logger:
    def __init__(self, log_file="bot.log"):
        self.log_file = log_file
        self.log_directory = "logs"
        self.ensure_log_directory()

    def ensure_log_directory(self):
        """Create logs directory if it doesn't exist"""
        if not os.path.exists(self.log_directory):
            os.makedirs(self.log_directory)

    def _log(self, level: str, message: str, color: str):
        """Internal method to handle logging with consistent formatting"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_message = f"[{timestamp}] [{level}] {message}"

        # Print to console with color
        print(f"{color}{log_message}{Style.RESET_ALL}")

        # Write to file without color codes
        with open(
            os.path.join(self.log_directory, self.log_file), "a", encoding="utf-8"
        ) as f:
            f.write(log_message + "\n")

    def info(self, message: str):
        """Log information messages in cyan"""
        self._log("INFO", message, Fore.CYAN)

    def success(self, message: str):
        """Log success messages in green"""
        self._log("SUCCESS", message, Fore.GREEN)

    def warning(self, message: str):
        """Log warning messages in yellow"""
        self._log("WARNING", message, Fore.YELLOW)

    def error(self, message: str):
        """Log error messages in red"""
        self._log("ERROR", message, Fore.RED)

    def critical(self, message: str):
        """Log critical messages in red with bright style"""
        self._log("CRITICAL", message, Fore.RED + Style.BRIGHT)

    def debug(self, message: str):
        """Log debug messages in magenta"""
        self._log("DEBUG", message, Fore.MAGENTA)


# Create a global logger instance
logger = Logger()
