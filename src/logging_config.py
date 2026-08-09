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

    # Save logs to a rotating log file
    file_handler = RotatingFileHandler(
        log_file,
        maxBytes=5*1024*1024,   # ~5 MB per log file
        backupCount=3,          # Keep 3 backup log files
        encoding="utf-8"
    )
    file_handler.setFormatter(formatter)

    # Configure the root logger
    root_logger = logging.getLogger()  # Get the root logger
    root_logger.setLevel(log_level)    # Set the log level for the root logger

    # Avoid adding duplicate handlers if setup_logging() is called again
    if not root_logger.handlers:
        root_logger.addHandler(console_handler)
        root_logger.addHandler(file_handler)

    # --- Silence third-party library logs ---
    logging.getLogger("google_genai").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("matplotlib").setLevel(logging.WARNING)