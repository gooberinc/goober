# If you're seeing this after cloning the Goober repo, note that this is a standalone module for translations.
# While it's used by Goober Core, it lives in its own repository and should not be modified here.
# For updates or contributions, visit: https://github.com/gooberinc/volta

import os
import json
import pathlib
import threading
import time
from dotenv import load_dotenv

ANSI = "\033["
RED = f"{ANSI}31m"
GREEN = f"{ANSI}32m"
YELLOW = f"{ANSI}33m"
DEBUG = f"{ANSI}1;30m"
RESET = f"{ANSI}0m"

load_dotenv()

LOCALE = os.getenv("locale")
module_dir = pathlib.Path(__file__).parent.parent
working_dir = pathlib.Path.cwd()
EXCLUDE_DIRS = {'.git', '__pycache__'}

locales_dirs = []

def find_locales_dirs(base_path):
    found = []
    for root, dirs, files in os.walk(base_path):
        dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS]

        if 'locales' in dirs:
            locales_path = pathlib.Path(root) / 'locales'
            found.append(locales_path)
            dirs.remove('locales')
    return found

locales_dirs.extend(find_locales_dirs(module_dir))
if working_dir != module_dir:
    locales_dirs.extend(find_locales_dirs(working_dir))

translations = {}
_file_mod_times = {}

def load_translations():
    global translations, _file_mod_times
    translations.clear()
    _file_mod_times.clear()

    for locales_dir in locales_dirs:
        for filename in os.listdir(locales_dir):
            if filename.endswith(".json"):
                lang_code = filename[:-5]
                file_path = locales_dir / filename
                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        data = json.load(f)
                    if lang_code not in translations:
                        translations[lang_code] = {}
                    translations[lang_code].update(data)
                    _file_mod_times[(lang_code, file_path)] = file_path.stat().st_mtime
                except Exception as e:
                    print(f"{RED}Failed loading {file_path}: {e}{RESET}")

def reload_if_changed():
    while True:
        for (lang_code, file_path), last_mtime in list(_file_mod_times.items()):
            try:
                current_mtime = file_path.stat().st_mtime
                if current_mtime != last_mtime:
                    print(f"{RED}Translation file changed: {file_path}, reloading...{RESET}")
                    load_translations()
                    break
            except FileNotFoundError:
                print(f"{RED}Translation file removed: {file_path}{RESET}")
                _file_mod_times.pop((lang_code, file_path), None)
                if lang_code in translations:
                    translations.pop(lang_code, None)

def set_language(lang: str):
    global LOCALE
    if lang in translations:
        LOCALE = lang
    else:
        print(f"{RED}Language '{lang}' not found, defaulting to 'en'{RESET}")
        LOCALE = "en"

def get_translation(lang: str, key: str):
    lang_translations = translations.get(lang, {})
    if key in lang_translations:
        return lang_translations[key]
    fallback = translations.get("en", {}).get(key, key)
    print(f"{RED}Missing key: '{key}' in language '{lang}', falling back to: '{fallback}'{RESET}") # yeah probably print this
    return fallback

def _(key: str) -> str:
    return get_translation(LOCALE, key)

load_translations()

watchdog_thread = threading.Thread(target=reload_if_changed, daemon=True)
watchdog_thread.start()
