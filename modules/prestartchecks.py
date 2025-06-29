import time
import os
import sys
import subprocess
import ast
import json
# import shutil
psutilavaliable = True
try:
    import requests
    import psutil
except ImportError:
    psutilavaliable = False
    print("Missing requests and psutil! Please install them using pip: `pip install requests psutil`")
import re
import importlib.metadata

from modules.globalvars import *


def check_requirements():
    STD_LIB_MODULES = {
        "os", "sys", "time", "ast", "asyncio", "re", "subprocess", "json",
        "datetime", "threading", "math", "logging", "functools", "itertools",
        "collections", "shutil", "socket", "types", "enum", "pathlib",
        "inspect", "traceback", "platform", "typing", "warnings", "email",
        "http", "urllib", "argparse", "io", "copy", "pickle", "gzip", "csv",
    }
    PACKAGE_ALIASES = {
        "discord": "discord.py",
        "better_profanity": "better-profanity",
        
    }

    parent_dir = os.path.dirname(os.path.abspath(__file__))
    requirements_path = os.path.join(parent_dir, '..', 'requirements.txt')
    requirements_path = os.path.abspath(requirements_path)

    if not os.path.exists(requirements_path):
        print(f"{RED}requirements.txt not found at {requirements_path} was it tampered with?{RESET}")
        return

    with open(requirements_path, 'r') as f:
        lines = f.readlines()
        requirements = {
            line.strip() for line in lines
            if line.strip() and not line.startswith('#')
        }

    cogs_dir = os.path.abspath(os.path.join(parent_dir, '..', 'cogs'))
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
                        print(f"{YELLOW}Warning: Failed to parse imports from {filename}: {e}{RESET}")
    else:
        print(f"{YELLOW}Cogs directory not found at {cogs_dir}, skipping scan.{RESET}")

    installed_packages = {dist.metadata['Name'].lower() for dist in importlib.metadata.distributions()}
    missing = []

    for req in sorted(requirements):
        if req in STD_LIB_MODULES or req == 'modules':
            print(f"{GREEN}STD LIB / LOCAL{RESET} {req} (skipped check)")
            continue

        check_name = PACKAGE_ALIASES.get(req, req).lower()

        if check_name in installed_packages:
            print(f"[{GREEN} OK {RESET}] {check_name}")
        else:
            print(f"[ {RED}MISSING{RESET} ] {check_name} is not installed")
            missing.append(check_name)

    if missing:
        print("\nMissing packages detected:")
        for pkg in missing:
            print(f"  - {pkg}")
        print(f"Telling goober central at {VERSION_URL}")
        payload = {
            "name": NAME,
            "version": local_version,
            "slash_commands": f"{slash_commands_enabled}\n\n**Error**\nMissing packages have been detected, Failed to start",
            "token": gooberTOKEN
        }
        try:
            response = requests.post(VERSION_URL + "/ping", json=payload)
        except Exception as e:
            print(f"{RED}Failed to contact {VERSION_URL}: {e}{RESET}")
        sys.exit(1)
    else:
        print("\nAll requirements are satisfied.")

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

            # Try to extract latency
            match = re.search(latency_pattern, result.stdout)
            if match:
                latency_ms = float(match.group(1))
                print(f"Ping to {host}: {latency_ms:.2f} ms")
                if latency_ms > 300:
                    print(f"{YELLOW}High latency detected! You may experience delays in response times.{RESET}")
            else:
                print(f"{YELLOW}Could not parse latency.{RESET}")

        else:
            print(result.stderr)
            print(f"{RED}Ping to {host} failed.{RESET}")

    except Exception as e:
        print(f"{RED}Error running ping: {e}{RESET}")

def check_memory():
    if psutilavaliable == False:
        return
    try:
        memory_info = psutil.virtual_memory()
        total_memory = memory_info.total / (1024 ** 3)
        used_memory = memory_info.used / (1024 ** 3)
        free_memory = memory_info.available / (1024 ** 3)

        print(f"Memory Usage: {used_memory:.2f} GB / {total_memory:.2f} GB ({(used_memory / total_memory) * 100:.2f}%)")
        if used_memory > total_memory * 0.9:
            print(f"{YELLOW}Memory usage is above 90% ({(used_memory / total_memory) * 100:.2f}%). Consider freeing up memory.{RESET}")
        print(f"Total Memory: {total_memory:.2f} GB")
        print(f"Used Memory: {used_memory:.2f} GB")

        if free_memory < 1:
            print(f"{RED}Low free memory detected! Only {free_memory:.2f} GB available.{RESET}")
            sys.exit(1)
    except ImportError:
        print("psutil is not installed. Memory check skipped.")

def check_cpu():
    if psutilavaliable == False:
        return
    print("Measuring CPU usage per core...")
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
        print(f"Core {idx}: {color}[{bar}] {core_usage:.2f}%{RESET}")

    total_cpu = sum(cpu_per_core) / len(cpu_per_core)
    print(f"Total CPU Usage: {total_cpu:.2f}%")

    if total_cpu > 85:
        print(f"{YELLOW}High average CPU usage: {total_cpu:.2f}%{RESET}")
    if total_cpu > 95:
        print(f"{RED}Really high CPU load! System may throttle or hang.{RESET}")
        sys.exit(1)

def check_memoryjson():
    try:
        print(f"Memory file: {os.path.getsize(MEMORY_FILE) / (1024 ** 2):.2f} MB")
        if os.path.getsize(MEMORY_FILE) > 1_073_741_824:
            print(f"{YELLOW}Memory file is 1GB or higher, consider clearing it to free up space.{RESET}")
        
        # Check for corrupted memory.json file
        try:
            with open(MEMORY_FILE, 'r', encoding='utf-8') as f:
                json.load(f)
        except json.JSONDecodeError as e:
            print(f"{RED}Memory file is corrupted! JSON decode error: {e}{RESET}")
            print(f"{YELLOW}Consider backing up and recreating the memory file.{RESET}")
        except UnicodeDecodeError as e:
            print(f"{RED}Memory file has encoding issues: {e}{RESET}")
            print(f"{YELLOW}Consider backing up and recreating the memory file.{RESET}")
        except Exception as e:
            print(f"{RED}Error reading memory file: {e}{RESET}")
            
    except FileNotFoundError:
        print(f"{YELLOW}Memory file not found.{RESET}")

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

def start_checks():
    print("Running pre-start checks...")
    check_requirements()
    check_latency()
    check_memory()
    check_memoryjson()
    check_cpu()
    print("Continuing in 5 seconds... Press any key to skip.")
    presskey2skip(timeout=5)
    
    os.system('cls' if os.name == 'nt' else 'clear')
    
    # i decided to experiment with this instead of the above line but it doesn't work too well so that's why i'm not using it
    # print("\n" * (shutil.get_terminal_size(fallback=(80, 24))).lines, end="")
    
    print(splashtext)