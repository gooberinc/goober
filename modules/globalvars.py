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
PURPLE = f"{ANSI}35m"
DEBUG = f"{ANSI}1;30m"
RESET = f"{ANSI}0m"
VERSION_URL = "https://goober.expect.ovh"
UPDATE_URL = VERSION_URL+"/latest_version.json"
LOCAL_VERSION_FILE = "current_version.txt" 
TOKEN = os.getenv("DISCORDBOTTOKEN", "0")
PREFIX = os.getenv("BOTPREFIX", "g.")
PING_LINE = os.getenv("PINGLINE")
CHECKS_DISABLED = os.getenv("CHECKSDISABLED")
LOCALE = os.getenv("LOCALE", "en")
gooberTOKEN = os.getenv("GOOBERTOKEN")
splashtext = os.getenv("SPLASHTEXT")
ownerid = int(os.getenv("OWNERID", "0"))
showmemenabled = os.getenv("SHOWMEMENABLED")
BLACKLISTED_USERS = os.getenv("BLACKLISTEDUSERS", "").split(",")
USERTRAIN_ENABLED = os.getenv("USERTRAINENABLED", "true").lower() == "true"
NAME = os.getenv("NAME")
MEMORY_FILE = "memory.json"
MEMORY_LOADED_FILE = "MEMORY_LOADED" # is this still even used?? okay just checked its used in the markov module
ALIVEPING = os.getenv("ALIVEPING")
AUTOUPDATE = os.getenv("AUTOUPDATE")
# IGNOREWARNING = False # is this either??? i don't think so?
song = os.getenv("song")
arch = platform.machine()
slash_commands_enabled = True # 100% broken, its a newer enough version so its probably enabled by default.... fix this at somepoint or hard code it in goober central code
launched = False
latest_version = "0.0.0"
local_version = "2.1.3"
os.environ['gooberlocal_version'] = local_version
REACT = os.getenv("REACT")
beta = True # this makes goober think its a beta version, so it will not update to the latest stable version or run any version checks
    