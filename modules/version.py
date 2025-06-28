from modules.translations import *
from modules.globalvars import *
import requests
import subprocess
import sys

# Run a shell command and return its output
def run_cmd(cmd):
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    return result.stdout.strip()

# Check if the remote branch is ahead of the local branch
def is_remote_ahead(branch='main', remote='origin'):
    run_cmd(f'git fetch {remote}')
    count = run_cmd(f'git rev-list --count HEAD..{remote}/{branch}')
    return int(count) > 0

# Automatically update the local repository if the remote is ahead
def auto_update(branch='main', remote='origin'):
    if AUTOUPDATE != "True":
        pass  # Auto-update is disabled
    if is_remote_ahead(branch, remote):
        print(f"Remote {remote}/{branch} is ahead. Updating...")
        pull_result = run_cmd(f'git pull {remote} {branch}')
        print(pull_result)
        print("Please Restart goober!")
        sys.exit(0)
    else:
        print(f"Local {remote}/{branch} is ahead and/or up to par. Not Updating...")

# Fetch the latest version info from the update server
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

# Check if an update is available and perform update if needed
def check_for_update():
    if ALIVEPING != "True":
        pass  # Update check is disabled
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

    # Check if local_version is valid
    if local_version == "0.0.0" or None:
        print(f"{RED}I cant find the local_version variable! Or its been tampered with and its not an interger!{RESET}")
        return

    # Compare local and latest versions
    if local_version < latest_version:
        print(f"{YELLOW}{get_translation(LOCALE, 'new_version').format(latest_version=latest_version, local_version=local_version)}{RESET}")
        print(f"{YELLOW}{get_translation(LOCALE, 'changelog').format(VERSION_URL=VERSION_URL)}{RESET}")
        auto_update()
    elif local_version == latest_version:
        print(f"{GREEN}{get_translation(LOCALE, 'latest_version')} {local_version}{RESET}")
        print(f"{get_translation(LOCALE, 'latest_version2').format(VERSION_URL=VERSION_URL)}\n\n")
    return latest_version