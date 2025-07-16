# If you're seeing this after cloning the Goober repo, note that this is a standalone module for translations.
# While it's used by Goober Core, it lives in its own repository and should not be modified here.
# For updates or contributions, visit: https://github.com/gooberinc/volta
# Also, Note to self: Add more comments it needs more love
import os
import locale
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

LOCALE = os.getenv("LOCALE")
module_dir = pathlib.Path(__file__).parent.parent
working_dir = pathlib.Path.cwd()
EXCLUDE_DIRS = {'.git', '__pycache__'}

locales_dirs = []
ENGLISH_MISSING = False
FALLBACK_LOCALE = "en"
if os.getenv("fallback_locale"):
    FALLBACK_LOCALE = os.getenv("fallback_locale")
def find_locales_dirs(base_path):
    found = []
    for root, dirs, files in os.walk(base_path):
        dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS]

        if 'locales' in dirs:
            locales_path = pathlib.Path(root) / 'locales'
            found.append(locales_path)
            dirs.remove('locales')
    return found

def find_dotenv(start_path: pathlib.Path) -> pathlib.Path | None:
    current = start_path.resolve()
    while current != current.parent:
        candidate = current / ".env"
        if candidate.exists():
            return candidate
        current = current.parent
    return None

env_path = find_dotenv(pathlib.Path(__file__).parent)
if env_path:
    load_dotenv(dotenv_path=env_path)
    print(f"[VOLTA] {GREEN}Loaded .env from {env_path}{RESET}")
else:
    print(f"[VOLTA] {YELLOW}No .env file found from {__file__} upwards.{RESET}")

locales_dirs.extend(find_locales_dirs(module_dir))
if working_dir != module_dir:
    locales_dirs.extend(find_locales_dirs(working_dir))

translations = {}
_file_mod_times = {}

import locale
import platform
import os
import sys

def get_system_locale():
    system = platform.system() # fallback incase locale isnt set
    if system == "Windows":
        lang, _ = locale.getdefaultlocale()
        return lang or os.getenv("LANG")
    elif system == "Darwin":
        try:
            import subprocess
            result = subprocess.run(
                ["defaults", "read", "-g", "AppleLocale"],
                stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL,
                text=True
            )
            return result.stdout.strip() or locale.getdefaultlocale()[0]
        except Exception:
            return locale.getdefaultlocale()[0]
    elif system == "Linux":
        return (
            os.getenv("LC_ALL") or
            os.getenv("LANG") or
            locale.getdefaultlocale()[0]
        )
    return locale.getdefaultlocale()[0]


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
    if not LOCALE:
        LOCALE = get_system_locale()
    elif lang in translations:
        LOCALE = lang
    else:
        print(f"[VOLTA] {RED}Language '{lang}' not found, defaulting to 'en'{RESET}")
        if FALLBACK_LOCALE in translations:
            LOCALE = FALLBACK_LOCALE
        else:
            print(f"[VOLTA] {RED}The fallback translations cannot be found! No fallback available.{RESET}")
            ENGLISH_MISSING = True

def check_missing_translations():
    global LOCALE, ENGLISH_MISSING
    load_translations()
    if FALLBACK_LOCALE not in translations:
        print(f"[VOLTA] {RED}Fallback translations ({FALLBACK_LOCALE}.json) missing from assets/locales.{RESET}")
        ENGLISH_MISSING = True
        return
    if LOCALE == "en":
        print("[VOLTA] Locale is English, skipping missing key check.")
        return
    

    en_keys = set(translations.get("en", {}).keys())
    locale_keys = set(translations.get(LOCALE, {}).keys())

    missing_keys = en_keys - locale_keys
    total_keys = len(en_keys)
    missing_count = len(missing_keys)

    if missing_count > 0:
        percent_missing = (missing_count / total_keys) * 100
        if percent_missing == 100:
            print(f"[VOLTA] {YELLOW}Warning: All keys are missing in locale '{LOCALE}'! Defaulting back to {FALLBACK_LOCALE}{RESET}")
            set_language(FALLBACK_LOCALE)
        elif percent_missing > 0:
            print(f"[VOLTA] {YELLOW}Warning: {missing_count}/{total_keys} keys missing in locale '{LOCALE}' ({percent_missing:.1f}%)!{RESET}")
            for key in sorted(missing_keys):
                print(f"  - {key}")
            time.sleep(2)
    else:
        print(f"[VOLTA] All translation keys present for locale: {LOCALE}")

printedsystemfallback = False

def get_translation(lang: str, key: str):
    global printedsystemfallback
    if ENGLISH_MISSING:
        return f"[VOLTA] {RED}No fallback available!{RESET}"
    fallback_translations = translations.get(FALLBACK_LOCALE, {})
    sys_lang = get_system_locale().split("_")[0] if get_system_locale() else None
    sys_translations = translations.get(sys_lang, {}) if sys_lang else {}
    lang_translations = translations.get(lang, {})
    if key in lang_translations:
        return lang_translations[key]
    if sys_lang and sys_lang != lang and key in sys_translations:
        if not printedsystemfallback:
            print(f"[VOLTA] {YELLOW}Falling back to system language {sys_lang}!{RESET}")
            printedsystemfallback = True
        return sys_translations[key]
    if key in fallback_translations:
        print(f"[VOLTA] {YELLOW}Missing key: '{key}' in '{lang}', falling back to fallback locale '{FALLBACK_LOCALE}'{RESET}")
        return fallback_translations[key]
    return f"[VOLTA] {YELLOW}Missing key: '{key}' in all locales!{RESET}"

def _(key: str) -> str:
    return get_translation(LOCALE, key)

load_translations()

watchdog_thread = threading.Thread(target=reload_if_changed, daemon=True)
watchdog_thread.start()

if __name__ == '__main__':
    print("Volta should not be run directly! Please use it as a module..")
