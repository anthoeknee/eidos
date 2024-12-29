import logging
import sys


class Logger:
    """
    A simple yet flexible logger with color output using the logging library.
    """

    # Define color codes as class variables
    RESET = "\033[0m"
    RED = "\033[31m"
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    BLUE = "\033[34m"
    MAGENTA = "\033[35m"
    CYAN = "\033[36m"

    # Add color mapping for different log levels
    LEVEL_COLORS = {
        "DEBUG": BLUE,
        "INFO": GREEN,
        "WARNING": YELLOW,
        "ERROR": RED,
        "CRITICAL": MAGENTA,
    }

    def __init__(self, name="default", level="INFO"):
        self.logger = logging.getLogger(name)

        # Clear any existing handlers
        if self.logger.handlers:
            self.logger.handlers.clear()

        # Set level
        self.logger.setLevel(getattr(logging, level.upper()))

        # Create custom formatter class to handle colors
        class ColorFormatter(logging.Formatter):
            def format(self, record):
                # Add color to the level name
                level_color = Logger.LEVEL_COLORS.get(record.levelname, Logger.RESET)
                record.levelname = f"{level_color}{record.levelname}{Logger.RESET}"
                return super().format(record)

        # Create formatter with the custom format
        formatter = ColorFormatter(
            f"{self.CYAN}[%(asctime)s]{self.RESET} [{name}] [%(levelname)s] %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )

        # Create console handler and set formatter
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)

        # Add handler
        self.logger.addHandler(console_handler)

        # Prevent propagation to root logger
        self.logger.propagate = False

    def __getattr__(self, name):
        """Delegate attribute access to the underlying logger."""
        return getattr(self.logger, name)


if __name__ == "__main__":
    logger = Logger(name="test_logger", level="DEBUG")
    logger.debug("This is a debug message.")
    logger.info("This is an info message.")
    logger.warning("This is a warning message.")
    logger.error("This is an error message.")
    logger.critical("This is a critical message.")

    logger_info = Logger(name="test_logger_info", level="INFO")
    logger_info.debug("This debug message should not appear")
    logger_info.info("This is an info message.")
    logger_info.warning("This is a warning message.")
    logger_info.error("This is an error message.")
    logger_info.critical("This is a critical message.")
