import os
import json
import pathlib
from modules.globalvars import RED, RESET

def load_translations():
    """
    Loads all translation JSON files from the 'locales' directory.
    Returns a dictionary mapping language codes to their translation dictionaries.
    """
    translations = {}
    # Get the path to the 'locales' directory (one level up from this file)
    translations_dir = pathlib.Path(__file__).parent.parent / 'locales'
    # Iterate over all files in the 'locales' directory
    for filename in os.listdir(translations_dir):
        if filename.endswith(".json"):
            # Extract language code from filename (e.g., 'en' from 'en.json')
            lang_code = filename.replace(".json", "")
            # Open and load the JSON file
            with open(os.path.join(translations_dir, filename), "r", encoding="utf-8") as f:
                translations[lang_code] = json.load(f)
    return translations

# Load all translations at module import
translations = load_translations()

def get_translation(lang: str, key: str):
    """
    Retrieves the translation for a given key and language.
    Falls back to English if the language is not found.
    Prints a warning if the key is missing.
    """
    # Get translations for the specified language, or fall back to English
    lang_translations = translations.get(lang, translations["en"])
    if key not in lang_translations:
        # Print a warning if the key is missing in the selected language
        print(f"{RED}Missing key: {key} in language {lang}{RESET}")
    # Return the translation if found, otherwise return the key itself
    return lang_translations.get(key, key)
