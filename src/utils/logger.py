# src/utils/logger.py
import logging
import sys
import os

# ANSI escape codes for colors
RESET = "\033[0m"
RED = "\033[31m"
GREEN = "\033[32m"
YELLOW = "\033[33m"
BLUE = "\033[34m"
MAGENTA = "\033[35m"
CYAN = "\033[36m"


def setup_logger():
    """Sets up the logger for the bot with color and a cleaner format."""
    logger = logging.getLogger("discord_bot")
    logger.setLevel(logging.DEBUG)
    logger.propagate = False

    file_handler = logging.FileHandler("bot.log", mode="w", encoding="utf-8")
    file_handler.setLevel(logging.DEBUG)

    stream_handler = logging.StreamHandler(sys.stdout)
    stream_handler.setLevel(logging.DEBUG)

    formatter = logging.Formatter(
        "%(asctime)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    file_handler.setFormatter(formatter)

    class ColoredFormatter(logging.Formatter):
        def format(self, record):
            log_message = super().format(record)
            if record.levelname == "DEBUG":
                return f"{CYAN}{log_message}{RESET}"
            elif record.levelname == "INFO":
                return f"{GREEN}{log_message}{RESET}"
            elif record.levelname == "WARNING":
                return f"{YELLOW}{log_message}{RESET}"
            elif record.levelname == "ERROR":
                return f"{RED}{log_message}{RESET}"
            elif record.levelname == "CRITICAL":
                return f"{RED}{MAGENTA}{log_message}{RESET}"
            else:
                return log_message

    colored_formatter = ColoredFormatter(
        f"%(asctime)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    stream_handler.setFormatter(colored_formatter)

    logger.addHandler(file_handler)
    logger.addHandler(stream_handler)

    return logger


logger = setup_logger()
