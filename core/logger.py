import logging
import os
from config import SystemConfig

SystemConfig.ensure_directories()
log_file = os.path.join(SystemConfig.LOGS_DIR, "app.log")
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s", handlers=[logging.FileHandler(log_file, encoding="utf-8"), logging.StreamHandler()])
app_logger = logging.getLogger("AppLogger")
