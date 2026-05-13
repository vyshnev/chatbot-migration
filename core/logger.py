import logging
import sys

# Define ANSI color codes for terminal output
class Colors:
    RESET = "\033[0m"
    INFO = "\033[94m"     # Blue
    WARNING = "\033[93m"  # Yellow
    ERROR = "\033[91m"    # Red
    DEBUG = "\033[90m"    # Gray
    TIME = "\033[32m"     # Green

class ColoredFormatter(logging.Formatter):
    """Custom formatter to add colors and a clean layout to terminal logs."""
    
    FORMATS = {
        logging.DEBUG: f"{Colors.TIME}%(asctime)s{Colors.RESET} | {Colors.DEBUG}DEBUG{Colors.RESET} | %(name)s:%(lineno)d | %(message)s",
        logging.INFO: f"{Colors.TIME}%(asctime)s{Colors.RESET} | {Colors.INFO}INFO{Colors.RESET}  | %(name)s:%(lineno)d | %(message)s",
        logging.WARNING: f"{Colors.TIME}%(asctime)s{Colors.RESET} | {Colors.WARNING}WARN{Colors.RESET}  | %(name)s:%(lineno)d | %(message)s",
        logging.ERROR: f"{Colors.TIME}%(asctime)s{Colors.RESET} | {Colors.ERROR}ERROR{Colors.RESET} | %(name)s:%(lineno)d | %(message)s",
        logging.CRITICAL: f"{Colors.TIME}%(asctime)s{Colors.RESET} | {Colors.ERROR}CRIT{Colors.RESET}  | %(name)s:%(lineno)d | %(message)s",
    }

    def format(self, record):
        log_fmt = self.FORMATS.get(record.levelno)
        formatter = logging.Formatter(log_fmt, datefmt="%Y-%m-%d %H:%M:%S")
        return formatter.format(record)

def get_logger(name: str) -> logging.Logger:
    """
    Returns a configured logger instance.
    Usage: logger = get_logger(__name__)
    """
    logger = logging.getLogger(name)
    
    # Only configure if it doesn't already have handlers to prevent duplicate logs
    if not logger.handlers:
        logger.setLevel(logging.INFO)
        
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(ColoredFormatter())
        
        logger.addHandler(console_handler)
        
        # Prevent log messages from propagating to the root logger
        logger.propagate = False
        
    return logger
