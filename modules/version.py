from modules.volta.main import _
from modules.globalvars import *
import requests
import subprocess
import sys
import logging
logger = logging.getLogger("goober")
launched = False

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
    if launched == True:
        print(_("already_started"))
        return
    if AUTOUPDATE != "True":
        pass  # Auto-update is disabled
    if is_remote_ahead(branch, remote):
        print(_( "remote_ahead").format(remote=remote, branch=branch))
        pull_result = run_cmd(f'git pull {remote} {branch}')
        logger.info(pull_result)
        logger.info(_( "please_restart"))
        sys.exit(0)
    else:
        logger.info(_( "local_ahead").format(remote=remote, branch=branch))

# Fetch the latest version info from the update server
def get_latest_version_info():
    try:
        response = requests.get(UPDATE_URL, timeout=5)
        if response.status_code == 200:
            return response.json()
        else:
            logger.error(f"{RED}{_( 'version_error')} {response.status_code}{RESET}")
            return None
    except requests.RequestException as e:
        logger.error(f"{RED}{_( 'version_error')} {e}{RESET}")
        return None

# Check if an update is available and perform update if needed
def check_for_update():
    if ALIVEPING != "True":
        return  
    global latest_version, local_version, launched

    latest_version_info = get_latest_version_info()
    if not latest_version_info:
        logger.error(f"{_('fetch_update_fail')}")
        return None, None

    latest_version = latest_version_info.get("version")
    os.environ['gooberlatest_version'] = latest_version
    download_url = latest_version_info.get("download_url")

    if not latest_version or not download_url:
        logger.error(f"{RED}{_(LOCALE, 'invalid_server')}{RESET}")
        return None, None

    # Check if local_version is valid
    if local_version == "0.0.0" or None:
        logger.error(f"{RED}{_('cant_find_local_version')}{RESET}")
        return

    # Compare local and latest versions
    if local_version < latest_version:
        logger.info(f"{YELLOW}{_('new_version').format(latest_version=latest_version, local_version=local_version)}{RESET}")
        logger.info(f"{YELLOW}{_('changelog').format(VERSION_URL=VERSION_URL)}{RESET}")
        auto_update()
    elif beta == True:
        logger.warning(f"You are running an \"unstable\" version of Goober, do not expect it to work properly.\nVersion {local_version}{RESET}")
    elif local_version > latest_version:
        logger.warning(f"{_('modification_warning')}")
    elif local_version == latest_version:
        logger.info(f"{_('latest_version')} {local_version}")
        logger.info(f"{_('latest_version2').format(VERSION_URL=VERSION_URL)}\n\n")
    launched = True
    return latest_version