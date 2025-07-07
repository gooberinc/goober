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
import importlib.metadata

# import shutil
psutilavaliable = True
try:
    import requests
    import psutil
except ImportError:
    psutilavaliable = False
    print(RED, _('missing_requests_psutil'), RESET)

def iscloned():
    if os.path.exists(".git"):
        return True
    else:
        print(f"{RED}{(_('not_cloned'))}{RESET}")
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
    }

    parent_dir = os.path.dirname(os.path.abspath(__file__))
    requirements_path = os.path.abspath(os.path.join(parent_dir, '..', 'requirements.txt'))

    if not os.path.exists(requirements_path):
        print(f"{RED}{(_('requirements_not_found')).format(path=requirements_path)}{RESET}")
        return

    with open(requirements_path, 'r') as f:
        lines = f.readlines()
        requirements = {
            line.strip() for line in lines
            if line.strip() and not line.startswith('#')
        }

    cogs_dir = os.path.abspath(os.path.join(parent_dir, '..', 'assets', 'cogs'))
    if os.path.isdir(cogs_dir):
        for filename in os.listdir(cogs_dir):
            if filename.endswith('.py'):
                filepath = os.path.join(cogs_dir, filename)
                with open(filepath, 'r', encoding='utf-8') as f:
                    try:
                        tree = ast.parse(f.read(), filename=filename)
                        for node in ast.walk(tree):
                            if isinstance(node, ast.Import):
                                for alias in node.names:
                                    pkg = alias.name.split('.')[0]
                                    if pkg in STD_LIB_MODULES or pkg == 'modules':
                                        continue
                                    requirements.add(pkg)
                            elif isinstance(node, ast.ImportFrom):
                                if node.module:
                                    pkg = node.module.split('.')[0]
                                    if pkg in STD_LIB_MODULES or pkg == 'modules':
                                        continue
                                    requirements.add(pkg)
                    except Exception as e:
                        print(f"{YELLOW}{(_('warning_failed_parse_imports')).format(filename=filename, error=e)}{RESET}")
    else:
        print(f"{YELLOW}{(_('cogs_dir_not_found')).format(path=cogs_dir)}{RESET}")

    installed_packages = {dist.metadata['Name'].lower() for dist in importlib.metadata.distributions()}
    missing = []

    for req in sorted(requirements):
        if req in STD_LIB_MODULES or req == 'modules':
            print((_('std_lib_local_skipped')).format(package=req))
            continue

        check_name = PACKAGE_ALIASES.get(req, req).lower()

        if check_name in installed_packages:
            print(f"[ {GREEN}{(_('ok_installed')).format(package=check_name)}{RESET} ] {check_name}")
        else:
            print(f"[ {RED}{(_('missing_package')).format(package=check_name)}{RESET} ] {check_name} {(_('missing_package2'))}")
            missing.append(check_name)

    if missing:
        print(RED, _('missing_packages_detected'), RESET)
        for pkg in missing:
            print(f"  - {pkg}")
        print((_('telling_goober_central')).format(url=VERSION_URL))
        payload = {
            "name": NAME,
            "version": local_version,
            "slash_commands": f"{slash_commands_enabled}\n\n**Error**\nMissing packages have been detected, Failed to start",
            "token": gooberTOKEN
        }
        try:
            requests.post(VERSION_URL + "/ping", json=payload)
        except Exception as e:
            print(f"{RED}{(_('failed_to_contact')).format(url=VERSION_URL, error=e)}{RESET}")
        sys.exit(1)
    else:
        print(_('all_requirements_satisfied'))

def check_latency():
    host = "1.1.1.1"

    system = platform.system()
    if system == "Windows":
        cmd = ["ping", "-n", "1", "-w", "1000", host]
        latency_pattern = r"Average = (\d+)ms"
    else:
        cmd = ["ping", "-c", "1", "-W", "1", host]
        latency_pattern = r"time[=<]\s*([\d\.]+)\s*ms"

    try:
        result = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )

        if result.returncode == 0:
            print(result.stdout)
            match = re.search(latency_pattern, result.stdout)
            if match:
                latency_ms = float(match.group(1))
                print((_('ping_to')).format(host=host, latency=latency_ms))
                if latency_ms > 300:
                    print(f"{YELLOW}{(_('high_latency'))}{RESET}")
            else:
                print(f"{YELLOW}{(_('could_not_parse_latency'))}{RESET}")
        else:
            print(result.stderr)
            print(f"{RED}{(_('ping_failed')).format(host=host)}{RESET}")
    except Exception as e:
        print(f"{RED}{(_('error_running_ping')).format(error=e)}{RESET}")

def check_memory():
    if psutilavaliable == False:
        return
    try:
        memory_info = psutil.virtual_memory()
        total_memory = memory_info.total / (1024 ** 3)
        used_memory = memory_info.used / (1024 ** 3)
        free_memory = memory_info.available / (1024 ** 3)

        print((_('memory_usage')).format(used=used_memory, total=total_memory, percent=(used_memory / total_memory) * 100))
        if used_memory > total_memory * 0.9:
            print(f"{YELLOW}{(_('memory_above_90')).format(percent=(used_memory / total_memory) * 100)}{RESET}")
        print((_('total_memory')).format(total=total_memory))
        print((_('used_memory')).format(used=used_memory))
        if free_memory < 1:
            print(f"{RED}{(_('low_free_memory')).format(free=free_memory)}{RESET}")
            sys.exit(1)
    except ImportError:
        print(_('psutil_not_installed')) # todo: translate this into italian and put it in the translations "psutil is not installed. Memory check skipped."

def check_cpu():
    if psutilavaliable == False:
        return
    print((_('measuring_cpu')))
    cpu_per_core = psutil.cpu_percent(interval=1, percpu=True)
    for idx, core_usage in enumerate(cpu_per_core):
        bar_length = int(core_usage / 5) 
        bar = '█' * bar_length + '-' * (20 - bar_length)
        if core_usage > 85:
            color = RED
        elif core_usage > 60:
            color = YELLOW
        else:
            color = GREEN
        print((_('core_usage')).format(idx=idx, bar=bar, usage=core_usage))
    total_cpu = sum(cpu_per_core) / len(cpu_per_core)
    print((_('total_cpu_usage')).format(usage=total_cpu))
    if total_cpu > 85:
        print(f"{YELLOW}{(_('high_avg_cpu')).format(usage=total_cpu)}{RESET}")
    if total_cpu > 95:
        print(f"{RED}{(_('really_high_cpu'))}{RESET}")
        sys.exit(1)

def check_memoryjson():
    try:
        print((_('memory_file')).format(size=os.path.getsize(MEMORY_FILE) / (1024 ** 2)))
        if os.path.getsize(MEMORY_FILE) > 1_073_741_824:
            print(f"{YELLOW}{(_('memory_file_large'))}{RESET}")
        try:
            with open(MEMORY_FILE, 'r', encoding='utf-8') as f:
                json.load(f)
        except json.JSONDecodeError as e:
            print(f"{RED}{(_('memory_file_corrupted')).format(error=e)}{RESET}")
            print(f"{YELLOW}{(_('consider_backup_memory'))}{RESET}")
        except UnicodeDecodeError as e:
            print(f"{RED}{(_('memory_file_encoding')).format(error=e)}{RESET}")
            print(f"{YELLOW}{(_('consider_backup_memory'))}{RESET}")
        except Exception as e:
            print(f"{RED}{(_('error_reading_memory')).format(error=e)}{RESET}")
    except FileNotFoundError:
        print(f"{YELLOW}{(_('memory_file_not_found'))}{RESET}")

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
        print(f"{YELLOW}{(_('checks_disabled'))}{RESET}")
        return
    print(_('running_prestart_checks'))
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
        print(f"{YELLOW}{(_('env_file_not_found'))}{RESET}")
        sys.exit(1)
    if beta == True:
        print(f"{YELLOW}this build isnt finished yet, some things might not work as expected{RESET}")
    else:
        pass
    print(_('continuing_in_seconds').format(seconds=5))
    presskey2skip(timeout=5)
    os.system('cls' if os.name == 'nt' else 'clear')
    print(splashtext)