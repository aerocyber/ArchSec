#!/usr/bin/python3

import os
import pathlib
import subprocess
from shutil import copyfile


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


# def grab_iso():
#     """
#         Download Arch ISO
#     """
#     url = "https://geo.mirror.pkgbuild.com/iso/2024.10.01/archlinux-x86_64.iso"
#     r = requests.get(url, allow_redirects=True)
#     f = open(url.split('/')[-1], 'wb')
#     f.write(r.content)
#     f.close()



def extract_iso(file_path: str):
    """
        Extract the iso to get the bootloader, kernel and other required files.\
        Args:
            file_path: str: Path to the arch iso image
    """
    cmd = f"osirrox -indev ../{file_path} -extract_boot_images ./ -extract /EFI/BOOT/BOOTx64.EFI grubx64.efi -extract /shellx64.efi shellx64.efi -extract /arch/boot/x86_64/vmlinuz-linux vmlinuz-linux"
    ret = subprocess.run(cmd, shell=True, capture_output=True)
    if ret.returncode != 0:
        print(f"Error: {ret.stderr.decode('utf-8')}")
        exit(1)
    cmd2 = "chmod +w *"
    ret2 = subprocess.run(cmd2, shell=True, capture_output=True)
    if ret2.returncode != 0:
        print(f"Error: {ret2.stderr.decode('utf-8')}")
    return 0


def get_shim_bin():
    """
        Get the shim binaries from `shim-signed`.
        The binaries MUST be located in `/usr/share/shim-signed/`
    """
    cmd1 = "cp /usr/share/shim-signed/shimx64.efi BOOTx64.EFI"
    cmd2 = "cp /usr/share/shim-signed/mmx64.efi ./"

    ret1 = subprocess.run(cmd1, shell=True, capture_output=True)
    if ret1.returncode != 0:
        print(f"Error: {ret1.stderr.decode('utf-8')}")
        exit(1)

    ret2 = subprocess.run(cmd2, shell=True, capture_output=True)
    if ret2.returncode != 0:
        print(f"Error: {ret2.stderr.decode('utf-8')}")
        exit(1)
    
    return 0


def sign_with_sbsigntools():
    """
        Signs the extracted and copied files with MOK.crt file
    """
    cmd1 = "sbsign --key MOK.key --cert MOK.crt --output grubx64.efi grubx64.efi"
    cmd2 = "sbsign --key MOK.key --cert MOK.crt --output shellx64.efi shellx64.efi"
    cmd3 = "sbsign --key MOK.key --cert MOK.crt --output vmlinuz-linux vmlinuz-linux"

    #### NOTE
    #### The following two signatures MAY NOT BE REQUIRED as THEY ARE ALREADY SIGNED.
    #### However, absence of the signature using the created MOK keys made the
    #### Bootable USB to NOT SHOW UP on my device.
    cmd4 = "sbsign --key ../MOK.key --cert MOK.crt --output BOOTx64.EFI BOOTx64.EFI"
    cmd5 = "sbsign --key ../MOK.key --cert MOK.crt --output mmx64.efi mmx64.efi"

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
    
    ret3 = subprocess.run(cmd3, shell=True, capture_output=True)
    if ret3.returncode != 0:
        print(f"Error: {ret3.stderr.decode('utf-8')}")
        exit(1)
    else:
        print(f"[INFO]: {ret3.stdout.decode('utf-8')}\n\n")

    ret4 = subprocess.run(cmd4, shell=True, capture_output=True)
    if ret4.returncode != 0:
        print(f"Error: {ret4.stderr.decode('utf-8')}")
        exit(1)
    else:
        print(f"[INFO]: {ret4.stdout.decode('utf-8')}\n\n")
    
    ret5 = subprocess.run(cmd5, shell=True, capture_output=True)
    if ret5.returncode != 0:
        print(f"Error: {ret5.stderr.decode('utf-8')}")
        exit(1)
    else:
        print(f"[INFO]: {ret5.stdout.decode('utf-8')}\n\n")

    return 0


def copy_to_image():
    """
        Copy the signed stuff to be loaded into ISO
    """
    cmd1 = "mcopy -D oO -i eltorito_img2_uefi.img vmlinuz-linux ::/arch/boot/x86_64/vmlinuz-linux"
    cmd2 = "mcopy -D oO -i eltorito_img2_uefi.img MOK.cer shellx64.efi ::/"
    cmd3 = "mcopy -D oO -i eltorito_img2_uefi.img BOOTx64.EFI grubx64.efi mmx64.efi ::/EFI/BOOT/"

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
    
    ret3 = subprocess.run(cmd3, shell=True, capture_output=True)
    if ret3.returncode != 0:
        print(f"Error: {ret3.stderr.decode('utf-8')}")
        exit(1)
    else:
        print(f"[INFO]: {ret3.stdout.decode('utf-8')}\n\n")

    return 0


def repack_iso(old_file_path: str, new_file_path: str):
    """
        Repack the ISO file.
        Args:
            old_file_path: str: Path to the Arch ISO Image
            new_file_path: str: Path to where the modified ISO is to be created. Must be a path to ISO file and not a directory.
    """
    cmd = f"xorriso -indev ../{old_file_path} -outdev {new_file_path} -map vmlinuz-linux /arch/boot/x86_64/vmlinuz-linux -map_l ./ / shellx64.efi MOK.cer -- -map_l ./ /EFI/BOOT/ BOOTx64.EFI grubx64.efi mmx64.efi -- -boot_image any replay -append_partition 2 0xef eltorito_img2_uefi.img"

    ret = subprocess.run(cmd, shell=True, capture_output=True)
    if ret.returncode != 0:
        print(f"Error: {ret.stderr.decode('utf-8')}")
        exit(1)
    else:
        print(f"[INFO]: {ret.stdout.decode('utf-8')}\n\n")

    return 0


def create_mok_keys():
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

def banner():
    banner_ = r"""
    _             _     ____            
   / \   _ __ ___| |__ / ___|  ___  ___ 
  / _ \ | '__/ __| '_ \\___ \ / _ \/ __|
 / ___ \| | | (__| | | |___) |  __/ (__ 
/_/   \_\_|  \___|_| |_|____/ \___|\___|
                                         
"""
    print(banner_)


if __name__ == '__main__':
    if not is_arch_based():
        print("This is not an Arch based system. Exiting...")
        exit(1)

    banner()

    print("Arch or Arch based system found. Ensure you have the following packages installed:")
    print("shim-signed - AUR")
    print("libisoburn - REPO")
    print("mtools - REPO")

    x = input("Continue? [Y/n]:\t")
    if not (x.upper() == 'Y' or x.upper() == "YES"):
        print("Exiting...")
        exit(0)

    cwd = os.getcwd()
    os.mkdir(f"{cwd}/archsec")

    archIso = input("Enter path to the Arch or Arch based ISO:\t")
    newArchIso = input("Enter path to the new ISO file. The file name must end with .iso and will be created if this script runs successfully:\t")

    if not pathlib.Path(archIso).exists():
        print("[ERROR]: File Not Found.\nExiting...")
        exit(1)

    mok_key = input("Enter path to MOK.key:\t")
    mok_cer = input("Enter path to MOK.cer:\t")
    mok_crt = input("Enter path to MOK.crt:\t")

    key_created = False

    if not (pathlib.Path(f"{cwd}/MOK.key").exists() or pathlib.Path(f"{cwd}/MOK.crt").exists() or pathlib.Path(f"{cwd}/MOK.cer").exists()):
        key_created = True
        create_mok_keys()

    if key_created == False and not (mok_cer.endswith('cer') and mok_crt('crt') and mok_key.endswith('key')):
        print("Invalid MOK extensions.\nExiting...")
        exit(1)
    
    os.chdir(f"{cwd}/archsec")
    copyfile(mok_cer, './MOK.cer')
    copyfile(mok_crt, './MOK.crt')
    copyfile(mok_key, './MOK.key')

    extract_iso(archIso)
    get_shim_bin()
    sign_with_sbsigntools()
    copy_to_image()
    repack_iso(archIso, newArchIso)
    
    
    print(f"Done... Check the iso file at: {newArchIso}")
    os.chdir(cwd)
