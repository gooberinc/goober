from modules.globalvars import *
from modules.volta.main import _, check_missing_translations
import time
import os
import sys
import subprocess
import sysconfig
import ast
import json
import re
from spacy.util import is_package
import importlib.metadata
import logging

logger = logging.getLogger("goober")

# import shutil
psutilavaliable = True
try:
    import requests
    import psutil
except ImportError:
    psutilavaliable = False
    logger.error(_('missing_requests_psutil'))

def check_for_model():
    if is_package("en_core_web_sm"):
        logger.info("Model is installed.")
    else:
        logger.info("Model is not installed.")

    
def iscloned():
    if os.path.exists(".git"):
        return True
    else:
        logger.error(f"{_('not_cloned')}") 
        sys.exit(1)

def get_stdlib_modules():
    stdlib_path = pathlib.Path(sysconfig.get_paths()['stdlib'])
    modules = set()
    if hasattr(sys, 'builtin_module_names'):
        modules.update(sys.builtin_module_names)
    for file in stdlib_path.glob('*.py'):
        if file.stem != '__init__':
            modules.add(file.stem)
    for folder in stdlib_path.iterdir():
        if folder.is_dir() and (folder / '__init__.py').exists():
            modules.add(folder.name)
    for file in stdlib_path.glob('*.*'):
        if file.suffix in ('.so', '.pyd'):
            modules.add(file.stem)

    return modules

def check_requirements():
    STD_LIB_MODULES = get_stdlib_modules()
    PACKAGE_ALIASES = {
        "discord": "discord.py",
        "better_profanity": "better-profanity",
        "dotenv": "python-dotenv",
        "pil": "pillow"
    }

    parent_dir = os.path.dirname(os.path.abspath(__file__))
    requirements_path = os.path.abspath(os.path.join(parent_dir, '..', 'requirements.txt'))

    if not os.path.exists(requirements_path):
        logger.error(f"{(_('requirements_not_found')).format(path=requirements_path)}")
        return

    with open(requirements_path, 'r') as f:
        lines = f.readlines()
        requirements = set()
        for line in lines:
            line = line.strip()
            if line and not line.startswith('#'):
                base_pkg = line.split('==')[0].lower()
                aliased_pkg = PACKAGE_ALIASES.get(base_pkg, base_pkg)
                requirements.add(aliased_pkg)

    installed_packages = {dist.metadata['Name'].lower() for dist in importlib.metadata.distributions()}
    missing = []

    for req in sorted(requirements):
        if req in STD_LIB_MODULES or req == 'modules':
            print((_('std_lib_local_skipped')).format(package=req))
            continue

        check_name = req.lower()

        if check_name in installed_packages:
            logger.info(f"{_('ok_installed').format(package=check_name)} {check_name}")
        else:
            logger.error(f"{(_('missing_package')).format(package=check_name)} {check_name} {(_('missing_package2'))}")
            missing.append(check_name)

    if missing:
        logger.error(_('missing_packages_detected'))
        for pkg in missing:
            print(f"  - {pkg}")
        sys.exit(1)
    else:
        logger.info(_('all_requirements_satisfied'))

def check_latency():
    host = "1.1.1.1"
    system = platform.system()

    if system == "Windows":
        cmd = ["ping", "-n", "1", "-w", "1000", host]
        latency_pattern = r"Average = (\d+)ms"

    elif system == "Darwin":
        cmd = ["ping", "-c", "1", host]
        latency_pattern = r"time=([\d\.]+) ms"

    else:
        cmd = ["ping", "-c", "1", "-W", "1", host]
        latency_pattern = r"time=([\d\.]+) ms"

    try:
        result = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )

        if result.returncode == 0:
            match = re.search(latency_pattern, result.stdout)
            if match:
                latency_ms = float(match.group(1))
                logger.info((_('ping_to')).format(host=host, latency=latency_ms))
                if latency_ms > 300:
                    logger.warning(f"{(_('high_latency'))}")
            else:
                logger.warning((_('could_not_parse_latency')))
        else:
            print(result.stderr)
            logger.error(f"{(_('ping_failed')).format(host=host)}{RESET}")
    except Exception as e:
        logger.error((_('error_running_ping')).format(error=e))

def check_memory():
    if psutilavaliable == False:
        return
    try:
        memory_info = psutil.virtual_memory()  # type: ignore
        total_memory = memory_info.total / (1024 ** 3)
        used_memory = memory_info.used / (1024 ** 3)
        free_memory = memory_info.available / (1024 ** 3)

        logger.info((_('memory_usage')).format(used=used_memory, total=total_memory, percent=(used_memory / total_memory) * 100))
        if used_memory > total_memory * 0.9:
            print(f"{YELLOW}{(_('memory_above_90')).format(percent=(used_memory / total_memory) * 100)}{RESET}")
        logger.info((_('total_memory')).format(total=total_memory))
        logger.info((_('used_memory')).format(used=used_memory))
        if free_memory < 1:
            logger.warning(f"{(_('low_free_memory')).format(free=free_memory)}")
            sys.exit(1)
    except ImportError:
        logger.error(_('psutil_not_installed')) # todo: translate this into italian and put it in the translations "psutil is not installed. Memory check skipped."

def check_cpu():
    if psutilavaliable == False:
        return
    logger.info((_('measuring_cpu')))
    cpu_per_core = psutil.cpu_percent(interval=1, percpu=True)  # type: ignore
    total_cpu = sum(cpu_per_core) / len(cpu_per_core)
    logger.info((_('total_cpu_usage')).format(usage=total_cpu))
    if total_cpu > 85:
        logger.warning(f"{(_('high_avg_cpu')).format(usage=total_cpu)}")
    if total_cpu > 95:
        logger.error(_('really_high_cpu'))
        sys.exit(1)

def check_memoryjson():
    try:
        logger.info((_('memory_file')).format(size=os.path.getsize(MEMORY_FILE) / (1024 ** 2)))
        if os.path.getsize(MEMORY_FILE) > 1_073_741_824:
            logger.warning(f"{(_('memory_file_large'))}")
        try:
            with open(MEMORY_FILE, 'r', encoding='utf-8') as f:
                json.load(f)
        except json.JSONDecodeError as e:
            logger.error(f"{(_('memory_file_corrupted')).format(error=e)}")
            logger.warning(f"{(_('consider_backup_memory'))}")
        except UnicodeDecodeError as e:
            logger.error(f"{(_('memory_file_encoding')).format(error=e)}")
            logger.warning(f"{(_('consider_backup_memory'))}")
        except Exception as e:
            logger.error(f"{(_('error_reading_memory')).format(error=e)}")
    except FileNotFoundError:
        logger(f"{(_('memory_file_not_found'))}")

def presskey2skip(timeout):
    if os.name == 'nt':
        import msvcrt
        start_time = time.time()
        while True:
            if msvcrt.kbhit():
                msvcrt.getch()
                break
            if time.time() - start_time > timeout:
                break
            time.sleep(0.1)
    else:
        import select
        import sys
        import termios
        import tty

        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)
        try:
            tty.setcbreak(fd)
            start_time = time.time()
            while True:
                if select.select([sys.stdin], [], [], 0)[0]:
                    sys.stdin.read(1)
                    break
                if time.time() - start_time > timeout:
                    break
                time.sleep(0.1)
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
beta = beta
def start_checks():
    if CHECKS_DISABLED == "True":
        logger.warning(f"{(_('checks_disabled'))}")
        return
    logger.info(_('running_prestart_checks'))
    check_for_model()
    iscloned()
    check_missing_translations()
    check_requirements()
    check_latency()
    check_memory()
    check_memoryjson()
    check_cpu()
    if os.path.exists(".env"):
        pass
    else:
        logger.warning(f"{(_('env_file_not_found'))}")
        sys.exit(1)
    if beta == True:
        logger.warning(f"this build isnt finished yet, some things might not work as expected")
    else:
        pass
    logger.info(_('continuing_in_seconds').format(seconds=5))
    presskey2skip(timeout=5)
    os.system('cls' if os.name == 'nt' else 'clear')
    print(splashtext)