"""Main entry point for cloud backup automation."""

import argparse
import logging
import sys
from pathlib import Path

from src.config import get_settings


def setup_logging(log_level: str = "INFO") -> None:
    """Configure application logging.
    
    Args:
        log_level: Logging level.
    """
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler("logs/cloud-backup.log"),
        ],
    )


def main() -> int:
    """Main entry point.
    
    Returns:
        Exit code (0 for success, non-zero for error).
    """
    parser = argparse.ArgumentParser(description="Monitors directory for new files and automatically backs them up to cloud storage")
    parser.add_argument(
        "--config",
        type=Path,
        help="Path to configuration file",
    )
    parser.add_argument(
        "--log-level",
        default="INFO",
        help="Logging level",
    )
    
    args = parser.parse_args()
    
    try:
        setup_logging(args.log_level)
        settings = get_settings()
        
        logging.info("Starting cloud backup")
        
        # TODO: Implement main logic
        
        return 0
    except KeyboardInterrupt:
        logging.warning("Interrupted by user")
        return 130
    except Exception as e:
        logging.error(f"Error: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())
