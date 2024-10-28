# About

This experimental set of scripts attempts to sign and repack Arch ISO for secure boot.
This script(s) requires the `archlinux-x86_64.iso` file to be in the same dir as the `make_sec_boot_iso.py` file.
Otherwise, it will be downloaded.

Run:

```bash
# pip install requests
python3 make_sec_boot_iso.py
```

## Warning

Use this script at your own risk. Author will NOT be responsible to damages caused not limited to loss of data, corrupted files and others.

To be run inside an Arch distro. Preferrably, inside an Arch Virtual Machine.

## Additional Steps

Apart from building the secure boot supported ISO, you must enroll the `DER` file. This varies between PCs and distros.

If you have `mokutils` installed on your distro, run: 

```bash
mokutil --import MOK.cer
```

where MOK.cer is the certificate file created by the script or otherwise. This command is to be run where the ISO is to be run.
Another way is to use the UEFI Firmware Interface. This varies between devices. Consult your manufacturer.

## Additional Info

If the `archlinux-x86_64.iso` file is not found, it will be downloaded.

If any of `MOK.cer`, `MOK.crt` or `MOK.key` is NOT found, the script will create them with `openssl`.

The script requires `requests` package from PyPI installed. Additionally, for the operations to be successful, the following packages must be installed:

- shim-signed from AUR
- libisoburn from Arch REPO
- mtools from Arch REPO
- openssl from Arch REPO

## License

Same as the licenses used by Arch Wiki
