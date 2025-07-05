import sys
import traceback
import os
from modules.globalvars import RED, RESET, splashtext
from modules.translations import _

def handle_exception(exc_type, exc_value, exc_traceback, *, context=None):
    os.system('cls' if os.name == 'nt' else 'clear')
    
    if issubclass(exc_type, KeyboardInterrupt):
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return

    print(splashtext)
    print(f"{RED}=====BEGINNING OF TRACEBACK====={RESET}")
    traceback.print_exception(exc_type, exc_value, exc_traceback)
    print(f"{RED}========END OF TRACEBACK========{RESET}")
    print(f"{RED}{_('unhandled_exception')}{RESET}")

    
    if context:
        print(f"{RED}Context: {context}{RESET}")



