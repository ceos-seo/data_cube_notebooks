# pylint: disable=logging-format-interpolation
""" Module for useful logging functionality. """
from os import path
from logging import handlers
from pathlib import Path
from types import SimpleNamespace
import logging

class Logger:
    """ Implements log handling.

    Attrs:
        lvl (SimpleNamespace): holds attributes for varying log levels and their values.
        logger: the logger instance.
    """
    def __init__(self, name='python', base_dir=path.dirname(path.abspath(__file__)), verbosity=1):
        """Initialize the logger."""
        Path(f'{base_dir}/log').mkdir(parents=True, exist_ok=True)

        # Setup verbosity checks
        self.lvl = SimpleNamespace(**logging._nameToLevel)
        verbosity = self.lvl.CRITICAL - (verbosity * 10)

        # Setup logging
        logging.captureWarnings(True)
        self.logger = logging.getLogger('py.warnings')
        self.logger.name = name
        self.logger.setLevel(self.lvl.DEBUG)

        # Setup logging to log.txt file with rotation
        file_handler = handlers.TimedRotatingFileHandler(f'{base_dir}/log/{name}.log',
                                                         when='d', interval=30,
                                                         backupCount=12)
        # Always log debug messages
        file_handler.setLevel(self.lvl.DEBUG)

        # Setup logging to stdout based on verbosity
        stdout_handler = logging.StreamHandler()
        stdout_handler.setLevel(verbosity)

        # Format the output message
        formatter = logging.Formatter(fmt='%(asctime)s %(name)s: %(levelname)s: %(message)s',
                                      datefmt='%b %d %H:%M:%S')
        file_handler.setFormatter(formatter)
        stdout_handler.setFormatter(formatter)

        # Setup the logging handler
        self.logger.addHandler(file_handler)
        self.logger.addHandler(stdout_handler)

    def log(self, msg, lvl=20):
        """Log a message based on the level passed.

        Args:
            lvl (int): The message level to log Default=20 (INFO).
            msg (str): The message to log.
        """
        self.logger.log(lvl, f'{msg}')
