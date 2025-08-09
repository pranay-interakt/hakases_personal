import os, logging
from logging.handlers import RotatingFileHandler
def get_logger(log_path: str):
  os.makedirs(os.path.dirname(log_path) or ".", exist_ok=True)
  lg = logging.getLogger("protocol_intel"); lg.setLevel(logging.INFO)
  if not lg.handlers:
    fh = RotatingFileHandler(log_path, maxBytes=2_000_000, backupCount=3)
    ch = logging.StreamHandler()
    fmt = logging.Formatter("%(asctime)s | %(levelname)s | %(message)s")
    fh.setFormatter(fmt); ch.setFormatter(fmt)
    lg.addHandler(fh); lg.addHandler(ch)
  return lg
