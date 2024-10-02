from datetime import date
import logging
from logging import handlers
import time

# https://stackoverflow.com/questions/384076
grey = '\033[0;37m'
yellow = '\033[0;33m'
red = '\033[1;31m'
bold_red = '\033[0;31m'
reset = '\033[0m'
format = '%(levelname)8s [%(asctime)s] %(name)21s | %(message)s'
datefmt = '%H:%M:%S'


class ColouredFormatter(logging.Formatter):
    FORMATS = {
        logging.DEBUG: grey + format + reset,
        logging.INFO: format,
        logging.WARNING: yellow + format + reset,
        logging.ERROR: red + format + reset,
        logging.CRITICAL: bold_red + format + reset
    }

    def format(self, record):
        log_fmt = self.FORMATS.get(record.levelno)
        formatter = logging.Formatter(log_fmt, self.datefmt)
        return formatter.format(record)


class BasicFormatter(logging.Formatter):
    FORMATS = {
        logging.DEBUG: format,
        logging.INFO: format,
        logging.WARNING: format,
        logging.ERROR: format,
        logging.CRITICAL: format
    }

    def format(self, record):
        log_fmt = self.FORMATS.get(record.levelno)
        formatter = logging.Formatter(log_fmt, self.datefmt)
        return formatter.format(record)


class CustomLogger(logging.Logger):
    def __init__(self, name, level=logging.INFO):
        super().__init__(name, level)

        console_handler = logging.StreamHandler()
        console_handler.setFormatter(ColouredFormatter(datefmt='%H:%M:%S'))

        today = date.today().isoformat()

        file_handler = handlers.TimedRotatingFileHandler(f'gwaff.log',
                                                   when='midnight',
                                                   backupCount=2)
        file_handler.setFormatter(BasicFormatter(datefmt='%H:%M:%S'))

        self.addHandler(console_handler)
        self.addHandler(file_handler)


logging.setLoggerClass(CustomLogger)


def Logger(name):
    return logging.getLogger(name)


if __name__ == '__main__':
    logger = Logger("LOGGER")
    logger.setLevel(logging.DEBUG)
    logger.debug("Debug message")
    logger.info("Info message")
    logger.warning("Warning message")
    logger.error("Error message")
    logger.critical("Crticial message")
