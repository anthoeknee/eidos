# start.py

import asyncio
import sys
import os

# Add the src directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.main import main
from src.utils.logger import Logger
from src.core.config import settings

# Initialize logger with the correct log level from settings
logger = Logger(name="Startup", level=settings.log_level)

if __name__ == "__main__":
    try:
        logger.info("Starting bot...")
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot shutdown requested by user")
    except Exception as e:
        logger.error(f"Fatal error occurred: {e}")
        logger.exception(e)
        sys.exit(1)
