# pylint: disable=fixme, line-too-long, invalid-name, superfluous-parens, trailing-whitespace, arguments-differ
import logging

class Logger():
    """A simple logger class that logs messages with the parent name."""

    def __init__(self, parentName, level = logging.INFO) -> None:
        self.logger = logging.getLogger(parentName)

        self.logger.setLevel(level)

        # Create a console handler and set the level
        ch = logging.StreamHandler()
        ch.setLevel(level)

        # Create a formatter
        formatter = logging.Formatter('[%(name)s] %(asctime)s [%(levelname)s] %(message)s')

        # Add the formatter to the console handler
        ch.setFormatter(formatter)

        # Add the console handler to the logger
        self.logger.addHandler(ch)

    def log(self, level, message):
        """Log a message with the given level."""
        self.logger.log(level, message)

    def error(self, message):
        """Log an error message."""
        self.log(logging.ERROR, message)

    def warn(self, message):
        """Log a warning message."""
        self.log(logging.WARNING, message)

    def info(self, message):
        """Log an info message."""
        self.log(logging.INFO, message)
