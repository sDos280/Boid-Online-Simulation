import logging
from colorlog import ColoredFormatter


def create_formatted_logger(level=logging.DEBUG):
    logger = logging.getLogger(__name__)
    if not logger.handlers:  # prevent duplicate handlers
        formatter = ColoredFormatter(
            "%(log_color)s%(levelname)-8s%(reset)s %(white)s%(message)s",
            log_colors={
                'DEBUG': 'cyan',
                'INFO': 'blue',
                'WARNING': 'yellow',
                'ERROR': 'red',
                'CRITICAL': 'bold_red',
            }
        )
        handler = logging.StreamHandler()
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(level)
    return logger
