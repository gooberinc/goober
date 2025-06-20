import os
import json
import pathlib
from modules.globalvars import RED, RESET
def load_translations():
    translations = {}
    translations_dir = pathlib.Path(__file__).parent.parent / 'locales'
    for filename in os.listdir(translations_dir):
        if filename.endswith(".json"):
            lang_code = filename.replace(".json", "")
            with open(os.path.join(translations_dir, filename), "r", encoding="utf-8") as f:
                translations[lang_code] = json.load(f)
    
    return translations

translations = load_translations()

def get_translation(lang: str, key: str):
    lang_translations = translations.get(lang, translations["en"])
    if key not in lang_translations:
        print(f"{RED}Missing key: {key} in language {lang}{RESET}")
    return lang_translations.get(key, key)
