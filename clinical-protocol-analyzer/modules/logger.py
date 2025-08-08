import logging
from logging.handlers import RotatingFileHandler

def get_logger(log_path: str) -> logging.Logger:
    logger = logging.getLogger("cpa")
    if logger.handlers:
        return logger
    logger.setLevel(logging.INFO)
    fmt = logging.Formatter("%(asctime)s | %(levelname)s | %(message)s")
    ch = logging.StreamHandler()
    ch.setFormatter(fmt)
    logger.addHandler(ch)
    if log_path:
        fh = RotatingFileHandler(log_path, maxBytes=2_000_000, backupCount=3)
        fh.setFormatter(fmt)
        logger.addHandler(fh)
    return logger
