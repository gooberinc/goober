import requests
import os
import modules.globalvars as gv
from modules.volta.main import _
from modules.markovmemory import get_file_info

# Ping the server to check if it's alive and send some info
def ping_server():
    if gv.ALIVEPING == "false":
        # If pinging is disabled, print message and set environment variable
        print(f"{gv.YELLOW}{(_('pinging_disabled'))}{gv.RESET}")
        os.environ['gooberauthenticated'] = 'No'
        return
    # Get server alert message
    goobres = requests.get(f"{gv.VERSION_URL}/alert")
    print(f"{(_('goober_server_alert'))}{goobres.text}")
    # Gather file info for payload
    file_info = get_file_info(gv.MEMORY_FILE)
    payload = {
        "name": gv.NAME,
        "memory_file_info": file_info,
        "version": gv.local_version,
        "slash_commands": gv.slash_commands_enabled,
        "token": gv.gooberTOKEN
    }
    try:
        # Send ping to server
        response = requests.post(gv.VERSION_URL+"/ping", json=payload)
        if response.status_code == 200:
            # Success: print message and set environment variable
            print(f"{gv.GREEN}{(_('goober_ping_success')).format(NAME=gv.NAME)}{gv.RESET}")
            os.environ['gooberauthenticated'] = 'Yes'
        else:
            # Failure: print error and set environment variable
            print(f"{gv.RED}{(_('goober_ping_fail'))} {response.status_code}{gv.RESET}")
            os.environ['gooberauthenticated'] = 'No'
    except Exception as e:
        # Exception: print error and set environment variable
        print(f"{gv.RED}{(_('goober_ping_fail2'))} {str(e)}{gv.RESET}")
        os.environ['gooberauthenticated'] = 'No'

# Check if a given name is available for registration
def is_name_available(NAME):
    if os.getenv("gooberTOKEN"):
        # If token is already set, skip check
        return
    try:
        # Send request to check name availability
        response = requests.post(f"{gv.VERSION_URL}/check-if-available", json={"name": NAME}, headers={"Content-Type": "application/json"})
        if response.status_code == 200:
            data = response.json()
            return data.get("available", False)
        else:
            # Print error if request failed
            print(f"{(_('name_check'))}", response.json())
            return False
    except Exception as e:
        # Print exception if request failed
        print(f"{(_('name_check2'))}", e)
        return False

# Register a new name with the server
def register_name(NAME):
    try:
        if gv.ALIVEPING == False:
            # If pinging is disabled, do nothing
            return
        # Check if the name is available
        if not is_name_available(NAME):
            if os.getenv("gooberTOKEN"):
                return
            # Name taken: print error and exit
            print(f"{gv.RED}{(_('name_taken'))}{gv.RESET}")
            quit()
        # Register the name
        response = requests.post(f"{gv.VERSION_URL}/register", json={"name": NAME}, headers={"Content-Type": "application/json"})
        if response.status_code == 200:
            data = response.json()
            token = data.get("token")
            if not os.getenv("gooberTOKEN"):
                # Print instructions to add token and exit
                print(f"{gv.GREEN}{(_('add_token')).format(token=token)} gooberTOKEN=<token>.{gv.gv.RESET}")
                quit()
            else:
                print(f"{gv.GREEN}{gv.gv.RESET}")
            return token
        else:
            # Print error if registration failed
            print(f"{gv.RED}{(_('token_exists')).format()}{gv.RESET}", response.json())
            return None
    except Exception as e:
        # Print exception if registration failed
        print(f"{gv.RED}{(_('registration_error')).format()}{gv.RESET}", e)
        return None

# Attempt to register the name at module load
register_name(gv.NAME)