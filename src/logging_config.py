import logging
from pathlib import Path
from logging.handlers import RotatingFileHandler


def setup_logging(config):
    log_config = config["logging"]

    log_level = getattr(
        logging,
        log_config["level"].upper()
    )

    log_file = log_config["file"]

    # Create the logs directory if it does not exist
    Path(log_file).parent.mkdir(parents=True, exist_ok=True)

    formatter = logging.Formatter(
        "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
    )

    # Show logs in the terminal
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)

    # Save logs to the log file
    file_handler = RotatingFileHandler(
        log_file,
        maxBytes=5*1024*1024,   # ~5 MB per log file
        backupCount=3,          # Keep 3 backup log files
        encoding="utf-8"
    )
    file_handler.setFormatter(formatter)

    # Configure the root logger
    logging.basicConfig(
        level=log_level,
        handlers=[
            console_handler,
            file_handler,
        ],
    )

    # --- Silence third-party library logs ---
    logging.getLogger("google_genai").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("matplotlib").setLevel(logging.WARNING)