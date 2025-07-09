import logging
from modules.globalvars import *

class GooberFormatter(logging.Formatter):
    def __init__(self, colors: bool = True): # Disable colors for TXT output
        self.colors = colors

        self._format = f"[ %(levelname)-8s ]: %(message)s {DEBUG} [%(asctime)s.%(msecs)03d] (%(filename)s:%(funcName)s) {RESET}"

        self.FORMATS = {
            logging.DEBUG: DEBUG + self._format + RESET,
            logging.INFO: self._format.replace("%(levelname)-8s", f"{GREEN}%(levelname)-8s{RESET}"),
            logging.WARNING: YELLOW + self._format + RESET,
            logging.ERROR: RED + self._format + RESET,
            logging.CRITICAL: PURPLE + self._format + RESET
        }

    def format(self, record: logging.LogRecord):
        if self.colors:
            log_fmt = self.FORMATS.get(record.levelno) # Add colors
        else:
            log_fmt = self._format # Just use the default format
            
        formatter = logging.Formatter(log_fmt, datefmt="%m/%d/%y %H:%M:%S")
        return formatter.format(record)
