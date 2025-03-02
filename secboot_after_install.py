#!/usr/bin/env python3

import subprocess
import os
from shutil import copyfile
from pathlib import Path

CRT_PATH = ''
KEY_PATH = ''
CER_PATH = ''

def is_arch_based():
    """Checks if the current OS is Arch-based using pacman.

    Returns:
        True if the OS is likely Arch-based, False otherwise.
    """

    try:
        subprocess.run(["pacman", "--version"])
    except Exception:
        return False

    return True

def is_root():
    return os.geteuid() == 0

# Create secure boot key
def create_secure_boot_keys():
    # We will use `mokutil` for key enrolling and `openssl` for creation of keys.
    cmd1 = 'openssl req -x509 -newkey rsa:2048 -keyout MOK.key -out MOK.crt -subj "/CN=Aero/"' # Replace Aero with your name!
    cmd2 = "openssl x509 -in MOK.crt -out MOK.cer -outform DER"

    ret1 = subprocess.run(cmd1, shell=True, capture_output=True)
    if ret1.returncode != 0:
        print(f"Error: {ret1.stderr.decode('utf-8')}")
        exit(1)
    else:
        print(f"[INFO]: {ret1.stdout.decode('utf-8')}\n\n")

    ret2 = subprocess.run(cmd2, shell=True, capture_output=True)
    if ret2.returncode != 0:
        print(f"Error: {ret2.stderr.decode('utf-8')}")
        exit(1)
    else:
        print(f"[INFO]: {ret2.stdout.decode('utf-8')}\n\n")

    key_file = str(Path(os.getcwd()).joinpath('MOK.key'))
    crt_file = str(Path(os.getcwd()).joinpath('MOK.crt'))

    path = '/secureboot/'
    count = 0
    while Path(path).exists():
        path = '/secureboot' + count + '/'
        count += 1

    CRT_PATH = path + 'MOK.crt'
    KEY_PATH = path + 'MOK.key'
    CER_PATH = os.getcwd() + '/MOK.cer'
    
    Path(path).mkdir()

    copyfile(key_file, '/secureboot/MOK.key')
    copyfile(crt_file, "/secureboot/MOK.crt")

    # Enroll secure boot key
    # Requires `mokutil` to be installed.
    # Package: mokutil
    print(f"Please run: mokutil --import {os.getcwd()}/MOK.cer")

def initcpico_setup():
    path = "/etc/initcpio/post/kernel-sbsign"
    cmd = "chmod +x /etc/initcpio/post/kernel-sbsign"

    content = [
        "#!/usr/bin/env bash\n",
        'kernel="$1"\n',
        '[[ -n "$kernel" ]] || exit 0\n',

        "# use already installed kernel if it exists\n",
        '[[ ! -f "$KERNELDESTINATION" ]] || kernel="$KERNELDESTINATION"\n\n',

        f'keypairs=({KEY_PATH} {CRT_PATH})\n'

        'for (( i=0; i<${#keypairs[@]}; i+=2 )); do\n',
        '    key="${keypairs[$i]}" cert="${keypairs[(( i + 1 ))]}"\n',
        '    if ! sbverify --cert "$cert" "$kernel" &>/dev/null; then\n',
        '        sbsign --key "$key" --cert "$cert" --output "$kernel" "$kernel"\n',
        '    fi\n',
        'done\n'
    ]

    with open(path, 'w') as f:
        f.writelines(content)

    subprocess.run(cmd)

def sign_bootmanager():
    ret2 = subprocess.run(f'sbsign --key {KEY_PATH} --cert {CRT_PATH} --output /boot/efi/EFI/BOOT/BOOTx64.EFI /boot/efi/EFI/BOOT/BOOTx64.EFI', shell=True, capture_output=True)
    if ret2.returncode != 0:
        print(f"Error: {ret2.stderr.decode('utf-8')}")
        exit(1)
    else:
        print(f"[INFO]: {ret2.stdout.decode('utf-8')}\n\n")

def banner():
    return r"""
    _             _     ____                                             
   / \   _ __ ___| |__ / ___|  ___  ___                                  
  / _ \ | '__/ __| '_ \\___ \ / _ \/ __|                                 
 / ___ \| | | (__| | | |___) |  __/ (__                                  
/_/   \_\_|  \___|_| |_|____/ \___|\___|                                 
 ____                 _     __ _              ___           _        _ _ 
/ ___|  ___  ___     / \   / _| |_ ___ _ __  |_ _|_ __  ___| |_ __ _| | |
\___ \ / _ \/ __|   / _ \ | |_| __/ _ \ '__|  | || '_ \/ __| __/ _` | | |
 ___) |  __/ (__   / ___ \|  _| ||  __/ |     | || | | \__ \ || (_| | | |
|____/ \___|\___| /_/   \_\_|  \__\___|_|    |___|_| |_|___/\__\__,_|_|_|
                                                                          
"""

if __name__ == '__main__':
    print(banner())

    if not is_arch_based():
        print("THE OS IS NOT BASED ON ARCH LINUX. EXITING")
        exit(1)

    if not is_root():
        subprocess.run(["pkexec", __file__])

    cwd = os.getcwd()

    print("Creating temporary directory and moving into it")
    os.mkdir('./tmp-archsec-secboot-after-install')
    os.chdir('./tmp-archsec-secboot-after-install')

    print("Making MOK keys")
    create_secure_boot_keys()
    print(f"Remember to run mokutil --import {CER_PATH}")

    print("Setting up kernel-sbsign")
    initcpico_setup()

    print("Signing boot manager")
    sign_bootmanager()

    os.chdir(cwd)
    os.rmdir('./tmp-archsec-secboot-after-install')

    print("Done!")
    exit(0)