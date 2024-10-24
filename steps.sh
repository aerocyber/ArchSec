#!/usr/bin/bash

# This script requires the arch iso be the latest x86_64 iso
# and in the same dir as this script.
# Tools requried are not installed or covered.
# For starters, this scrip needs the following packages in fedora (I used f40 for this):
# openssl
# sbsigntools
# xorriso
# 

# Make a work dir and cd into it
mkdir work_dir
cd work_dir

# Make machine owner key (MOK)
openssl req -newkey rsa:2048 -nodes -keyout MOK.key -new -x509 -sha256 -days 3650 -subj "/CN=my Machine Owner Key/" -out MOK.crt
openssl x509 -outform DER -in MOK.crt -out MOK.cer

# Enroll key
# Varies between the tool... for fedora run: sudo mokutil --import mok.cer

# Extract
osirrox -indev ../archlinux-x86_64.iso \
	-extract_boot_images ./ \
	-cpx /arch/boot/x86_64/vmlinuz-linux \
	/EFI/BOOT/BOOTx64.EFI \
	/EFI/BOOT/BOOTIA32.EFI \
	/shellx64.efi \
	/shellia32.efi ./

# Add w bit
chmod +w BOOTx64.EFI BOOTIA32.EFI shellx64.efi shellia32.efi vmlinuz-linux

# Sign it
sbsign --key MOK.key --cert MOK.crt --output BOOTx64.EFI BOOTx64.EFI
sbsign --key MOK.key --cert MOK.crt --output BOOTIA32.EFI BOOTIA32.EFI
sbsign --key MOK.key --cert MOK.crt --output shellx64.efi shellx64.efi
sbsign --key MOK.key --cert MOK.crt --output shellia32.efi shellia32.efi
sbsign --key MOK.key --cert MOK.crt --output vmlinuz-linux vmlinuz-linux

# Copy the binaries
mcopy -D oO -i eltorito_img2_uefi.img vmlinuz-linux ::/arch/boot/x86_64/vmlinuz-linux
mcopy -D oO -i eltorito_img2_uefi.img BOOTx64.EFI BOOTIA32.EFI ::/EFI/BOOT/
mcopy -D oO -i eltorito_img2_uefi.img shellx64.efi shellia32.efi ::/

# Repack
xorriso -indev ../archlinux-x86_64.iso -outdev archlinux-secure-boot-x86_64.iso \
        -map vmlinuz-linux /arch/boot/x86_64/vmlinuz-linux \
        -map_l ./ /EFI/BOOT/ BOOTx64.EFI BOOTIA32.EFI -- \
        -map_l ./ / shellx64.efi shellia32.efi -- \
        -boot_image any replay \
        -append_partition 2 0xef eltorito_img2_uefi.img
