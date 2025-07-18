# src/global_logger.py

import logging
import os, sys
from datetime import datetime
from .config_handler import ConfigHandler, get_default_config_path


class GlobalLogger:
    config = ConfigHandler()

    @classmethod
    def get_logger(cls, name):
        base_path = os.path.dirname(get_default_config_path())
        log_subpath = cls.config.get('Logging', 'path')
        log_level = cls.config.get('Logging', 'loglevel')

        log_dir = os.path.join(base_path, log_subpath)

        logger = logging.getLogger(name)
        logger.setLevel(getattr(logging, log_level.upper(), logging.INFO))

        if not os.path.exists(log_dir):
            os.makedirs(log_dir)

        # Create a log file with the current date
        current_date = datetime.now().strftime("%Y-%m-%d")
        log_file = os.path.join(log_dir, f"{current_date}.log")

        # Create a file handler with the new log file
        handler = logging.FileHandler(log_file, encoding='utf-8')
        handler.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] [%(name)s] %(message)s"))

        console_handler = logging.StreamHandler()
        console_handler.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] [%(name)s] %(message)s"))

        # Remove previous handlers if they exist to avoid duplicate logs
        if logger.hasHandlers():
            logger.handlers.clear()

        logger.addHandler(handler)
        logger.addHandler(console_handler)

        return logger
