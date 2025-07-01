import os
import platform
from dotenv import load_dotenv
import pathlib

env_path = pathlib.Path(__file__).parent.parent / '.env'
load_dotenv(dotenv_path=env_path)

ANSI = "\033["
RED = f"{ANSI}31m"
GREEN = f"{ANSI}32m"
YELLOW = f"{ANSI}33m"
DEBUG = f"{ANSI}1;30m"
RESET = f"{ANSI}0m"
VERSION_URL = "https://goober.expect.ovh"
UPDATE_URL = VERSION_URL+"/latest_version.json"
LOCAL_VERSION_FILE = "current_version.txt" 
TOKEN = os.getenv("DISCORD_BOT_TOKEN", "0")
PREFIX = os.getenv("BOT_PREFIX", "g.")
hourlyspeak = int(os.getenv("hourlyspeak", "0"))
PING_LINE = os.getenv("PING_LINE")
LOCALE = os.getenv("locale", "en")
gooberTOKEN = os.getenv("gooberTOKEN")
cooldown_time = os.getenv("cooldown")
splashtext = os.getenv("splashtext")
ownerid = int(os.getenv("ownerid", "0"))
showmemenabled = os.getenv("showmemenabled")
BLACKLISTED_USERS = os.getenv("BLACKLISTED_USERS", "").split(",")
USERTRAIN_ENABLED = os.getenv("USERTRAIN_ENABLED", "true").lower() == "true"
NAME = os.getenv("NAME")
MEMORY_FILE = "memory.json"
DEFAULT_DATASET_FILE = "defaultdataset.json"
MEMORY_LOADED_FILE = "MEMORY_LOADED"
ALIVEPING = os.getenv("ALIVEPING")
AUTOUPDATE = os.getenv("AUTOUPDATE")
IGNOREWARNING = False
song = os.getenv("song")
arch = platform.machine()
slash_commands_enabled = False
launched = False
latest_version = "0.0.0"
local_version = "1.0.4"
os.environ['gooberlocal_version'] = local_version
