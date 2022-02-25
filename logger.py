"""container-loading-problem - logger.py
---- AUTHOR: Ivan STEPANIAN (iv-stpn <iv.stpn@gmail.com>)
---- ROLE: Defines logger-related utils (logger variable, display_info decorator)
"""

from datetime import datetime
import logging
from typing import Callable
from yachalk import chalk

# Name of the app, used in the shared logger of the folder
APP_NAME = "container-loading"

# Custom formatting to be used by the CustomFormatter
LOGGER_FORMAT = "[%(levelname)s] %(asctime)s — %(message)s (%(filename)s:%(lineno)d)"
FORMATS = {
    logging.DEBUG: chalk.blue(LOGGER_FORMAT),
    logging.INFO: chalk.green(LOGGER_FORMAT),
    logging.WARNING: chalk.yellow(LOGGER_FORMAT),
    logging.ERROR: chalk.red(LOGGER_FORMAT),
    logging.CRITICAL: chalk.bold.red(LOGGER_FORMAT),
}


class CustomFormatter(logging.Formatter):
    """Defines a custom format by implementing the format method of logging.Formatter.

    Formats are defined in the FORMATS constant.
    """

    def format(self, record: logging.LogRecord) -> str:
        """Creates a new formatter that formats the given record.

        Args:
            record (logging.LogRecord): The LogRecord passed to the formatter.

        Returns:
            str: The formatted string returned by the newly constructed Formatter.
        """
        return logging.Formatter(FORMATS[record.levelno]).format(record)


def change_log_level(log_level: str) -> None:
    """Sets the log level of logger to a new log level passed as a string.
    Using logging.getLevelName to get the level ID and setLevel to set the log level of logger.

    Args:
        log_level (str): The string form of a log level, converted to a level ID by
        logging.getLevelName.
    """
    logger.setLevel(logging.getLevelName(log_level))
    ch.setLevel(logging.getLevelName(log_level))


# The shared custom logger in the project folder
logger = logging.getLogger(APP_NAME)

# StreamHandler (on sys.error) used to set the custom formatting
ch = logging.StreamHandler()
ch.setFormatter(CustomFormatter())

# FileHandler on custom log file (default name is <current_datetime>.log)
log_file = logging.FileHandler(
    f'logs/{datetime.now().strftime("%d-%m-%Y %H-%M-%S")}.log'
)

logger.addHandler(ch)
logger.addHandler(log_file)

# Sets the log level of logger to a custom default
LOG_LEVEL = "CRITICAL"
change_log_level(LOG_LEVEL)


def display_info(f: Callable) -> Callable:
    """Decorator used to force the log level of logger to INFO within the context of a function.
    The log level of logger is then reset back to LOG_LEVEL.

    Args:
        f (Callable): A function in which the log level of logger will be force-set to INFO.
    """

    def custom_f(*args, **kwargs):
        if kwargs.get("debug", False):
            change_log_level("INFO")
            output = f(*args, **kwargs)
            change_log_level(LOG_LEVEL)
        else:
            output = f(*args, **kwargs)

        return output

    return custom_f
