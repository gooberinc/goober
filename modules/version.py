import hashlib
from modules.translations import *
from modules.globalvars import *
import traceback
import requests

def generate_sha256_of_current_file():
    global currenthash
    sha256_hash = hashlib.sha256()
    with open(__file__, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    currenthash = sha256_hash.hexdigest()

def get_latest_version_info():

    try:

        response = requests.get(UPDATE_URL, timeout=5)
        if response.status_code == 200:
            return response.json()
        else:
            print(f"{RED}{get_translation(LOCALE, 'version_error')} {response.status_code}{RESET}")
            return None
    except requests.RequestException as e:
        print(f"{RED}{get_translation(LOCALE, 'version_error')} {e}{RESET}")
        return None
    
def check_for_update():
    if ALIVEPING == "false":
        return
    global latest_version, local_version 
    
    latest_version_info = get_latest_version_info()
    if not latest_version_info:
        print(f"{get_translation(LOCALE, 'fetch_update_fail')}")
        return None, None 

    latest_version = latest_version_info.get("version")
    os.environ['gooberlatest_version'] = latest_version
    download_url = latest_version_info.get("download_url")

    if not latest_version or not download_url:
        print(f"{RED}{get_translation(LOCALE, 'invalid_server')}{RESET}")
        return None, None 

    if local_version == "0.0.0" or None:
        print(f"{RED}I cant find the local_version variable! Or its been tampered with and its not an interger!{RESET}")
        return

    generate_sha256_of_current_file()
    gooberhash = latest_version_info.get("hash")
    if local_version < latest_version:
        print(f"{YELLOW}{get_translation(LOCALE, 'new_version').format(latest_version=latest_version, local_version=local_version)}{RESET}")
        print(f"{YELLOW}{get_translation(LOCALE, 'changelog').format(VERSION_URL=VERSION_URL)}{RESET}")

    elif local_version == latest_version:
        print(f"{GREEN}{get_translation(LOCALE, 'latest_version')} {local_version}{RESET}")
        print(f"{get_translation(LOCALE, 'latest_version2').format(VERSION_URL=VERSION_URL)}\n\n")

        # finally fucking fixed this i tell you
        if gooberhash != currenthash:
            print(f"{YELLOW}{get_translation(LOCALE, 'modification_warning')}{RESET}")
            print(f"{YELLOW}{get_translation(LOCALE, 'reported_version')} {local_version}{RESET}")
            print(f"{DEBUG}{get_translation(LOCALE, 'current_hash')} {currenthash}{RESET}")
    print(f"{DEBUG}{get_translation(LOCALE, 'current_hash')} {currenthash}{RESET}")

