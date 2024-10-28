#!/usr/bin/python3

import os
import pathlib
import subprocess
import requests

from shutil import copyfile


def is_arch_based():
    """Checks if the current OS is Arch-based using pacman.

    Returns:
        True if the OS is likely Arch-based, False otherwise.
    """

    try:
        subprocess.check_output(["pacman", "--version"])
        return True
    except subprocess.CalledProcessError:
        pass

    return False


def grab_iso():
    """
        Download Arch ISO
    """
    url = "https://geo.mirror.pkgbuild.com/iso/2024.10.01/archlinux-x86_64.iso"
    r = requests.get(url, allow_redirects=True)
    f = open(url.split('/')[-1], 'wb')
    f.write(r.content)
    f.close()



def extract_iso():
    """
        Extract the iso to get the bootloader, kernel and other required files.
    """
    cmd = "osirrox -indev ../archlinux-x86_64.iso -extract_boot_images ./ -extract /EFI/BOOT/BOOTx64.EFI grubx64.efi -extract /shellx64.efi shellx64.efi -extract /arch/boot/x86_64/vmlinuz-linux vmlinuz-linux"
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
        Get the shim binaries from `shim-signed`
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


def repack_iso():
    """
        Repack the ISO file.
    """
    cmd = "xorriso -indev ../archlinux-x86_64.iso -outdev archlinux-secure-boot-shim-x86_64.iso -map vmlinuz-linux /arch/boot/x86_64/vmlinuz-linux -map_l ./ / shellx64.efi MOK.cer -- -map_l ./ /EFI/BOOT/ BOOTx64.EFI grubx64.efi mmx64.efi -- -boot_image any replay -append_partition 2 0xef eltorito_img2_uefi.img"

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


if __name__ == '__main__':
    if not is_arch_based():
        print("This is not an Arch based system. Exiting...")
        exit(1)

    print("Arch or Arch based system found. Ensure you have the following packages installed:")
    print("shim-signed - AUR")
    print("libisoburn - REPO")
    print("mtools - REPO")

    cwd = os.getcwd()
    os.mkdir(f"{cwd}/archsec")

    if not pathlib.Path(f"{cwd}/archlinux-x86_64.iso").exists():
        grab_iso()

    if not (pathlib.Path(f"{cwd}/MOK.key").exists() or pathlib.Path(f"{cwd}/MOK.crt").exists() or pathlib.Path(f"{cwd}/MOK.cer").exists()):
        create_mok_keys()

    os.chdir(f"{cwd}/archsec")
    copyfile("../MOK.cer", './MOK.cer')
    copyfile("../MOK.crt", './MOK.crt')
    copyfile("../MOK.key", './MOK.key')

    extract_iso()
    get_shim_bin()
    sign_with_sbsigntools()
    copy_to_image()
    repack_iso()
    
    
    print(f"Done... Check the iso file: archlinux-secure-boot-shim-x86_64.iso at: {cwd}/archsec")
    os.chdir(cwd)
