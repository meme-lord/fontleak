import logging
import sys
from logging import Formatter

# Add color support
class ColorFormatter(Formatter):
    grey = "\x1b[38;20m"
    yellow = "\x1b[33;20m"
    red = "\x1b[31;20m"
    bold_red = "\x1b[31;1m"
    reset = "\x1b[0m"
    format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

    FORMATS = {
        logging.DEBUG: grey + format + reset,
        logging.INFO: grey + format + reset,
        logging.WARNING: yellow + format + reset,
        logging.ERROR: red + format + reset,
        logging.CRITICAL: bold_red + format + reset
    }

    def format(self, record):
        log_fmt = self.FORMATS.get(record.levelno)
        formatter = logging.Formatter(log_fmt, datefmt="%Y-%m-%d %H:%M:%S")
        return formatter.format(record)

# Configure logger
logger = logging.getLogger("fontleak")
logger.setLevel(logging.DEBUG)

# Console handler with color
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setLevel(logging.INFO)

# Only use color formatter if output is a terminal
if sys.stdout.isatty():
    console_handler.setFormatter(ColorFormatter())
else:
    console_handler.setFormatter(logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s"))

# Add handler
logger.addHandler(console_handler)