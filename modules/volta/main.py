# If you're seeing this after cloning the Goober repo, note that this is a standalone module for translations.
# While it's used by Goober Core, it lives in its own repository and should not be modified here.
# For updates or contributions, visit: https://github.com/gooberinc/volta
# Also, Note to self: Add more comments it needs more love
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
ENGLISH_MISSING = False

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
                    print(f"[VOLTA] {RED}Failed loading {file_path}: {e}{RESET}")

def reload_if_changed():
    while True:
        for (lang_code, file_path), last_mtime in list(_file_mod_times.items()):
            try:
                current_mtime = file_path.stat().st_mtime
                if current_mtime != last_mtime:
                    print(f"[VOLTA] {RED}Translation file changed: {file_path}, reloading...{RESET}")
                    load_translations()
                    break
            except FileNotFoundError:
                print(f"[VOLTA] {RED}Translation file removed: {file_path}{RESET}")
                _file_mod_times.pop((lang_code, file_path), None)
                if lang_code in translations:
                    translations.pop(lang_code, None)

def set_language(lang: str):
    global LOCALE, ENGLISH_MISSING
    if lang in translations:
        LOCALE = lang
    else:
        print(f"[VOLTA] {RED}Language '{lang}' not found, defaulting to 'en'{RESET}")
        if "en" in translations:
            LOCALE = "en"
        else:
            print(f"[VOLTA] {RED}The English translations cannot be found! No fallback available.{RESET}")
            ENGLISH_MISSING = True

def check_missing_translations():
    global LOCALE, ENGLISH_MISSING
    load_translations()
    if "en" not in translations:
        print(f"[VOLTA] {RED}English translations (en.json) missing from assets/locales. Exiting.{RESET}")
        ENGLISH_MISSING = True
        return
    if LOCALE == "en":
        print("Locale is English, skipping missing key check.")
        return
    

    en_keys = set(translations.get("en", {}).keys())
    locale_keys = set(translations.get(LOCALE, {}).keys())

    missing_keys = en_keys - locale_keys
    total_keys = len(en_keys)
    missing_count = len(missing_keys)

    if missing_count > 0:
        percent_missing = (missing_count / total_keys) * 100
        if percent_missing == 100:
            print(f"[VOLTA] {RED}Warning: All keys are missing in locale '{LOCALE}'! Defaulting back to en{RESET}")
            set_language("en")
        elif percent_missing > 0:
            print(f"{YELLOW}Warning: {missing_count}/{total_keys} keys missing in locale '{LOCALE}' ({percent_missing:.1f}%)!{RESET}")
            for key in sorted(missing_keys):
                print(f"  - {key}")
            time.sleep(2)
    else:
        print("All translation keys present for locale:", LOCALE)


def get_translation(lang: str, key: str):
    if ENGLISH_MISSING:
        return f"[VOLTA] {RED}No fallback available!{RESET}"
    lang_translations = translations.get(lang, {})
    if key in lang_translations:
        return lang_translations[key]
    fallback = translations.get("en", {}).get(key, key)
    print(f"[VOLTA] {RED}Missing key: '{key}' in language '{lang}', falling back to: '{fallback}'{RESET}") # yeah probably print this
    return fallback

def _(key: str) -> str:
    return get_translation(LOCALE, key)

load_translations()

watchdog_thread = threading.Thread(target=reload_if_changed, daemon=True)
watchdog_thread.start()

