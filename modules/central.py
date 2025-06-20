import requests
import os
import modules.globalvars as gv
from modules.translations import *
from modules.markovmemory import get_file_info

def ping_server():
    if gv.ALIVEPING == "false":
        print(f"{gv.YELLOW}{get_translation(gv.LOCALE, 'pinging_disabled')}{RESET}")
        os.environ['gooberauthenticated'] = 'No'
        return
    goobres = requests.get(f"{gv.VERSION_URL}/alert")
    print(f"{get_translation(gv.LOCALE, 'goober_server_alert')}{goobres.text}")
    file_info = get_file_info(gv.MEMORY_FILE)
    payload = {
        "name": gv.NAME,
        "memory_file_info": file_info,
        "version": gv.local_version,
        "slash_commands": gv.slash_commands_enabled,
        "token": gv.gooberTOKEN
    }
    try:
        response = requests.post(gv.VERSION_URL+"/ping", json=payload)
        if response.status_code == 200:
            print(f"{gv.GREEN}{get_translation(gv.LOCALE, 'goober_ping_success').format(NAME=gv.NAME)}{RESET}")
            os.environ['gooberauthenticated'] = 'Yes'
        else:
            print(f"{RED}{get_translation(gv.LOCALE, 'goober_ping_fail')} {response.status_code}{RESET}")
            os.environ['gooberauthenticated'] = 'No'
    except Exception as e:
        print(f"{RED}{get_translation(gv.LOCALE, 'goober_ping_fail2')} {str(e)}{RESET}")
        os.environ['gooberauthenticated'] = 'No'

def is_name_available(NAME):
    if os.getenv("gooberTOKEN"):
        return
    try:
        response = requests.post(f"{gv.VERSION_URL}/check-if-available", json={"name": NAME}, headers={"Content-Type": "application/json"})
        
        if response.status_code == 200:
            data = response.json()
            return data.get("available", False)
        else:
            print(f"{get_translation(gv.LOCALE, 'name_check')}", response.json())
            return False
    except Exception as e:
        print(f"{get_translation(gv.LOCALE, 'name_check2')}", e)
        return False

def register_name(NAME):
    try:
        if gv.ALIVEPING == False:
            return
        # check if the name is avaliable
        if not is_name_available(NAME):
            if os.getenv("gooberTOKEN"):
                return
            print(f"{RED}{get_translation(gv.LOCALE, 'name_taken')}{RESET}")
            quit()
        
        # if it is register it
        response = requests.post(f"{gv.VERSION_URL}/register", json={"name": NAME}, headers={"Content-Type": "application/json"})
        
        if response.status_code == 200:
            data = response.json()
            token = data.get("token")
            
            if not os.getenv("gooberTOKEN"):
                print(f"{gv.GREEN}{get_translation(gv.LOCALE, 'add_token').format(token=token)} gooberTOKEN=<token>.{gv.RESET}")
                quit()
            else:
                print(f"{gv.GREEN}{gv.RESET}")
            
            return token
        else:
            print(f"{gv.RED}{get_translation(gv.LOCALE, 'token_exists').format()}{RESET}", response.json())
            return None
    except Exception as e:
        print(f"{gv.RED}{get_translation(gv.LOCALE, 'registration_error').format()}{RESET}", e)
        return None

register_name(gv.NAME)