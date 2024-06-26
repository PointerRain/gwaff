import logging
import time

# https://stackoverflow.com/questions/384076
grey = '\033[0;37m'
yellow = '\033[0;33m'
red = '\033[1;31m'
bold_red = '\033[0;31m'
reset = '\033[0m'
format = '%(levelname)8s [%(asctime)s] %(name)21s | %(message)s'
datefmt = '%H:%M:%S'


class CustomFormatter(logging.Formatter):
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


class CustomLogger(logging.Logger):
    def __init__(self, name, level=logging.INFO):
        super().__init__(name, level)
        console = logging.StreamHandler()
        console.setFormatter(CustomFormatter(datefmt='%H:%M:%S'))
        self.addHandler(console)

logging.setLoggerClass(CustomLogger)

def Logger(name):
    return logging.getLogger(name)



class Colors:
    """ ANSI color codes """
    BLACK = "\033[0;30m"
    RED = "\033[0;31m"
    GREEN = "\033[0;32m"
    BROWN = "\033[0;33m"
    BLUE = "\033[0;34m"
    PURPLE = "\033[0;35m"
    CYAN = "\033[0;36m"
    LIGHT_GRAY = "\033[0;37m"
    DARK_GRAY = "\033[1;30m"
    LIGHT_RED = "\033[1;31m"
    LIGHT_GREEN = "\033[1;32m"
    YELLOW = "\033[1;33m"
    LIGHT_BLUE = "\033[1;34m"
    LIGHT_PURPLE = "\033[1;35m"
    LIGHT_CYAN = "\033[1;36m"
    LIGHT_WHITE = "\033[1;37m"
    BOLD = "\033[1m"
    FAINT = "\033[2m"
    ITALIC = "\033[3m"
    # UNDERLINE = "\033[4m"
    # BLINK = "\033[5m"
    # NEGATIVE = "\033[7m"
    # CROSSED = "\033[9m"
    END = "\033[0m"
    # # cancel SGR codes if we don't write to a terminal
    # if not __import__("sys").stdout.isatty():
    #     for _ in dir():
    #         if isinstance(_, str) and _[0] != "_":
    #             locals()[_] = ""
    # else:
    #     # set Windows console in VT mode
    #     if __import__("platform").system() == "Windows":
    #         kernel32 = __import__("ctypes").windll.kernel32
    #         kernel32.SetConsoleMode(kernel32.GetStdHandle(-11), 7)
    #         del kernel32


if __name__ == '__main__':
    logger = Logger("LOGGER")
    logger.setLevel(logging.DEBUG)
    logger.debug("Debug message")
    logger.info("Info message")
    logger.warning("Warning message")
    logger.error("Error message")
    logger.critical("Crticial message")

    input()

    for i in dir(Colors):
        if i[0:1] != "_" and i != "END":
            print("{:>16} {}".format(i, getattr(Colors, i) + i + Colors.END))

    input()