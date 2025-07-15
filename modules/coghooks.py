import os
import importlib
import inspect
import sys

_hooks = {}

def register_hook(name, func):
    if name not in _hooks:
        _hooks[name] = []
    _hooks[name].append(func)

async def call_hook(name, *args, **kwargs):
    if name not in _hooks:
        return
    for func in _hooks[name]:
        if callable(func):
            if inspect.iscoroutinefunction(func):
                await func(*args, **kwargs)
            else:
                func(*args, **kwargs)

def register_all_functions_as_hooks(module):
    """Register every function/coroutine function in the given module as a hook under its function name."""
    for name, obj in inspect.getmembers(module):
        if inspect.isfunction(obj) or inspect.iscoroutinefunction(obj):
            register_hook(name, obj)

def _register_all_modules_functions():
    """Scan all python modules in this 'modules' folder (excluding this file) and register their functions."""
    # Calculate the path to the modules directory relative to this file
    modules_dir = os.path.dirname(os.path.abspath(__file__))

    # Current file name so we skip it
    current_file = os.path.basename(__file__)

    # Ensure 'modules' is in sys.path for importlib to work
    if modules_dir not in sys.path:
        sys.path.insert(0, modules_dir)

    # List all python files except dunder files and this file
    for filename in os.listdir(modules_dir):
        if filename.endswith(".py") and not filename.startswith("__") and filename != current_file:
            module_name = filename[:-3]  # strip .py extension
            try:
                module = importlib.import_module(module_name)
                register_all_functions_as_hooks(module)
            except Exception as e:
                print(f"[hooks] Failed to import {module_name}: {e}")


