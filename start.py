#!/usr/bin/env python3
import sys
from pathlib import Path


def main():
    """
    Start script that ensures proper Python path setup.
    This allows the bot to be started from any directory while maintaining correct imports.
    """
    # Get the absolute path to the project root
    project_root = Path(__file__).parent.absolute()

    # Add the project root to Python path to enable imports
    sys.path.insert(0, str(project_root))

    # Import and run the bot's main function
    from src.main import main
    import asyncio

    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nBot shutdown requested by user")
    except Exception as e:
        print(f"Error starting bot: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
