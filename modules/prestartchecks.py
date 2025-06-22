import time
import os
import psutil
import sys
import subprocess
import ast
import requests
import importlib.metadata

from modules.globalvars import *
from ping3 import ping

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
    
    host = "1.1.1.1" # change this to google later
    latency = ping(host)

    if latency is not None:
        print(f"Ping to {host}: {latency * 1000:.2f} ms")
        if latency * 1000 > 300:
            print(f"{YELLOW}High latency detected! You may experience delays in response times.{RESET}")
    else:
        print("Ping failed.")

def check_memory():
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

def check_memoryjson():
    try:
        print(f"Memory file: {os.path.getsize(MEMORY_FILE) / (1024 ** 2):.2f} MB")
        if os.path.getsize(MEMORY_FILE) == 1_073_741_824:
            print(f"{YELLOW}Memory file is 1GB, consider clearing it to free up space.{RESET}")
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
        print("Continuing in 5 seconds... Press any key to skip.")
        presskey2skip(5)
        os.system('cls' if os.name == 'nt' else 'clear')
        print(splashtext)