try:
    import sys
    import subprocess
    import os
    import shutil
    import traceback
    import time
    import datetime
except ImportError as e:
    print(f"[X] Failed to load required module, likely not installed: {e}")
    try:
        sys.exit(1)
    except:
        exit(1)

if os.geteuid() != 0:
    print("[X] This script must be run as root.")
    sys.exit(1)


delta = time.time()

DATE = datetime.datetime.now().strftime("%Y.%m.%d")

print(f'[*] Beginning build for PassKill-{DATE}...')


RELEASE_CODE_NAME="plucky"
MIRROR="http://mirror.pilotfiber.com/ubuntu/"
CHROOT_DIR=os.path.join(os.getcwd(), "chroot")
IMAGE_DIR=os.path.join(os.getcwd(), "image")
APT_CACHE=os.path.join(os.getcwd(), ".apt-cache")
APT_LISTS=os.path.join(os.getcwd(), ".apt-lists")
ISO_VOLID=f"PassKill-{DATE}"
OUTPUT=os.path.join(os.getcwd(), "build", f"PassKill-{DATE}.iso")
MD5_OUTPUT=os.path.join(os.getcwd(), "build", f"PassKill-{DATE}.iso.md5")


os.makedirs(APT_CACHE, exist_ok=True)
os.makedirs(APT_LISTS, exist_ok=True)


if os.path.exists(OUTPUT):
    if input(f"Output file \"{OUTPUT}\" already exists, continue? [Y/n]: ").lower() == "y":
        os.remove(OUTPUT)
    else:
        print("[*] Exiting...")
        sys.exit(0)


print("[*] Checking dependencies...")
dependencies = ["debootstrap", "mksquashfs", "xorriso"]

for dep in dependencies:
    if not shutil.which(dep):
        print(f"[X] {dep} is not installed. Please install it to continue.")
        sys.exit(1)

try:
    print("[*] Creating chroot environment...")
    try:
        os.makedirs(CHROOT_DIR, exist_ok=False)
    except Exception as e:
        traceback.print_exc()
        print("[X] Failed to create chroot folder, might already exist.")
        sys.exit(1)

    try:
        subprocess.run(["debootstrap", 
                            "--arch=amd64", 
                            "--variant=minbase", 
                            "--cache-dir="+APT_CACHE,
                            "--include=python3,python3-requests",
                            RELEASE_CODE_NAME, 
                            CHROOT_DIR, 
                            MIRROR],
                        check=True)
    except Exception as e:
        traceback.print_exc()
        print(f"[X] Failed to create chroot environment")
        sys.exit(1)
    
    print("[*] Preparing chroot...")
    try:
        with open(os.path.join(CHROOT_DIR, "etc", "apt", "sources.list"), "w") as f:
            f.write(f"""
deb {MIRROR} {RELEASE_CODE_NAME} main restricted universe multiverse
deb-src {MIRROR} {RELEASE_CODE_NAME} main restricted universe multiverse

deb {MIRROR} {RELEASE_CODE_NAME}-security main restricted universe multiverse
deb-src {MIRROR} {RELEASE_CODE_NAME}-security main restricted universe multiverse

deb {MIRROR} {RELEASE_CODE_NAME}-updates main restricted universe multiverse
deb-src {MIRROR} {RELEASE_CODE_NAME}-updates main restricted universe multiverse
""".strip())
        
        subprocess.run(["cp", "chroot.py", os.path.join(CHROOT_DIR, "chroot.py")], check=True)
        os.makedirs(os.path.join(CHROOT_DIR, "usr", "share", "plymouth", "themes"), exist_ok=True)
        subprocess.run(["cp", "-r", os.path.join(os.getcwd(), "plymouth"), os.path.join(CHROOT_DIR, "usr", "share", "plymouth", "themes", "passkill")], check=True)
        os.makedirs(os.path.join(CHROOT_DIR, 'usr', 'share', 'icons'), exist_ok=True)
        subprocess.run(["cp", os.path.join(os.getcwd(), 'exit_gnome.png'), os.path.join(CHROOT_DIR, 'usr', 'share', 'icons', 'exit_gnome.png')], check=True)
        subprocess.run(["chown", "-R", "root:root", os.path.join(CHROOT_DIR, "usr", "share", "plymouth", "themes", "passkill")], check=True)

        DEV_DIR = os.path.join(CHROOT_DIR, "dev")

        # mount a private /dev
        subprocess.run(["mount", "-t", "tmpfs", "tmpfs", DEV_DIR], check=True)

        # make essential device nodes
        subprocess.run(["mknod", "-m", "666", os.path.join(DEV_DIR, "null"), "c", "1", "3"], check=True)
        subprocess.run(["mknod", "-m", "666", os.path.join(DEV_DIR, "zero"), "c", "1", "5"], check=True)
        subprocess.run(["mknod", "-m", "666", os.path.join(DEV_DIR, "random"), "c", "1", "8"], check=True)
        subprocess.run(["mknod", "-m", "666", os.path.join(DEV_DIR, "urandom"), "c", "1", "9"], check=True)
        subprocess.run(["mknod", "-m", "666", os.path.join(DEV_DIR, "tty"), "c", "5", "0"], check=True)
        subprocess.run(["mknod", "-m", "600", os.path.join(DEV_DIR, "console"), "c", "5", "1"], check=True)
        subprocess.run(["mknod", "-m", "666", os.path.join(DEV_DIR, "full"), "c", "1", "7"], check=True)
        subprocess.run(["mknod", "-m", "666", os.path.join(DEV_DIR, "ptmx"), "c", "5", "2"], check=True)

        # symlink fd -> /proc/self/fd
        subprocess.run(["ln", "-s", "/proc/self/fd", os.path.join(DEV_DIR, "fd")], check=True)

        subprocess.run(["mount", "-t", "tmpfs", "tmpfs", os.path.join(CHROOT_DIR, "run")], check=True)
        subprocess.run(["mount", "--bind", APT_CACHE, os.path.join(CHROOT_DIR, "var", "cache", "apt", "archives")], check=True)
        subprocess.run(["mount", "--bind", APT_LISTS, os.path.join(CHROOT_DIR, "var", "lib", "apt", "lists")], check=True)


        print("[*] Entering chroot...")
        try:
            subprocess.run(["chroot", CHROOT_DIR, "/usr/bin/env", "python3", "chroot.py"], check=True)
        except Exception as e:
            traceback.print_exc()
            print("[X] Failed to enter chroot")
            sys.exit(1)
        
    except Exception as e:
        traceback.print_exc()
        print("[X] Failed to prepare chroot")
        sys.exit(1)
    finally:
        print("[*] Unbinding chroot mounts...")
        subprocess.run(["umount", os.path.join(CHROOT_DIR, "dev", "pts")], check=False)
        subprocess.run(["umount", os.path.join(CHROOT_DIR, "proc")], check=False)
        subprocess.run(["umount", os.path.join(CHROOT_DIR, "sys")], check=False)
        subprocess.run(["umount", os.path.join(CHROOT_DIR, "dev")], check=False)
        subprocess.run(["umount", os.path.join(CHROOT_DIR, "run")], check=False)
        subprocess.run(["umount", os.path.join(CHROOT_DIR, "var", "cache", "apt", "archives")], check=False)
        subprocess.run(["umount", os.path.join(CHROOT_DIR, "var", "lib", "apt", "lists")], check=False)
        os.remove(os.path.join(CHROOT_DIR, "chroot.py"))
    
    
    print("[*] Creating squashfs...")
    try:
        os.rename(os.path.join(CHROOT_DIR, "image"), IMAGE_DIR)

        subprocess.run(["mksquashfs", CHROOT_DIR, os.path.join(IMAGE_DIR, "casper", "filesystem.squashfs"), 
                        "-noappend", "-no-duplicates", "-no-recovery", 
                        "-wildcards", 
                        "-comp", "zstd", "-b", "1M",
                        "-e", "var/cache/apt/archives/*",
                        "-e", "root/*",
                        "-e", "root/.*",
                        "-e", "tmp/*",
                        "-e", "tmp/.*",
                        "-e", "swapfile"])

        size = subprocess.check_output(
            ["du", "-sx", "--block-size=1", CHROOT_DIR],
            text=True
        ).split()[0]

        print(size)

        open(os.path.join(IMAGE_DIR, "casper", "filesystem.size"), "w").write(size)
    except Exception as e:
        traceback.print_exc()
        print("[X] Failed to create squashfs")
        sys.exit(1)
    

    print("[*] Creating ISO...")
    try:
        os.makedirs(os.path.dirname(OUTPUT), exist_ok=True)

        subprocess.run([
            "xorriso",
                "-as", "mkisofs",
                "-iso-level", "3",
                "-full-iso9660-filenames",
                "-J", "-J", "-joliet-long",
                "-volid", ISO_VOLID,
                "-output", OUTPUT,
                "-eltorito-boot", "isolinux/bios.img",
                    "-no-emul-boot",
                    "-boot-load-size", "4",
                    "-boot-info-table",
                    "--eltorito-catalog", "boot.catalog",
                    "--grub2-boot-info",
                    "--grub2-mbr", "../chroot/usr/lib/grub/i386-pc/boot_hybrid.img",
                    "-partition_offset", "16",
                    "--mbr-force-bootable",
                "-eltorito-alt-boot",
                    "-no-emul-boot",
                    "-e", "isolinux/efiboot.img",
                    "-append_partition", "2", "28732ac11ff8d211ba4b00a0c93ec93b", "isolinux/efiboot.img",
                    "-appended_part_as_gpt",
                    "-iso_mbr_part_type", "a2a0d0ebe5b9334487c068b6b72699c7",
                    "-m", "isolinux/efiboot.img",
                    "-m", "isolinux/bios.img",
                    "-e", "--interval:appended_partition_2:::",
                "-exclude", "isolinux",
                "-graft-points",
                    "/EFI/boot/bootx64.efi=isolinux/bootx64.efi",
                    "/EFI/boot/mmx64.efi=isolinux/mmx64.efi",
                    "/EFI/boot/grubx64.efi=isolinux/grubx64.efi",
                    "/EFI/ubuntu/grub.cfg=isolinux/grub.cfg",
                    "/isolinux/bios.img=isolinux/bios.img",
                    "/isolinux/efiboot.img=isolinux/efiboot.img",
                    "."
        ], check=True, cwd=IMAGE_DIR)
    except:
        traceback.print_exc()
        print("[X] Failed to create ISO")
        sys.exit(1)

    
    print("[*] Creating md5 hash file...")
    try:
        subprocess.run(["md5sum", OUTPUT], check=True, stdout=open(MD5_OUTPUT, "w"))
    except:
        traceback.print_exc()
        print("[X] Failed to create md5 hash file, skipping...")
        # MD5 is not needed
        

except Exception as e:
    traceback.print_exc()
    print("[X] Unknown failure.")
    sys.exit(1)
finally:
    print("[*] Cleaning up...")
    if os.path.exists(IMAGE_DIR):
        shutil.rmtree(IMAGE_DIR)
    
    if os.path.exists(CHROOT_DIR):
        time.sleep(5)
        subprocess.run(["umount", os.path.join(CHROOT_DIR, "dev", "pts")], check=False)
        subprocess.run(["umount", os.path.join(CHROOT_DIR, "proc")], check=False)
        subprocess.run(["umount", os.path.join(CHROOT_DIR, "sys")], check=False)
        subprocess.run(["umount", os.path.join(CHROOT_DIR, "dev")], check=False)
        subprocess.run(["umount", os.path.join(CHROOT_DIR, "run")], check=False)
        subprocess.run(["umount", os.path.join(CHROOT_DIR, "var", "cache", "apt", "archives")], check=False)
        subprocess.run(["umount", os.path.join(CHROOT_DIR, "var", "lib", "apt", "lists")], check=False)

        if os.path.ismount(os.path.join(CHROOT_DIR, "proc")):
            print("[X] Failed to unmount /proc, not cleaning up root jail.")
        elif os.path.ismount(os.path.join(CHROOT_DIR, "sys")):
            print("[X] Failed to unmount /sys, not cleaning up root jail.")
        elif os.path.ismount(os.path.join(CHROOT_DIR, "dev", "pts")):
            print("[X] Failed to unmount /dev/pts, not cleaning up root jail.")
        elif os.path.ismount(os.path.join(CHROOT_DIR, "dev")):
            print("[X] Failed to unmount /dev, not cleaning up root jail.")
        elif os.path.ismount(os.path.join(CHROOT_DIR, "run")):
            print("[X] Failed to unmount /run, not cleaning up root jail.")
        elif os.path.ismount(os.path.join(CHROOT_DIR, "var", "cache", "apt", "archives")):
            print("[X] Failed to unmount /var/cache/apt/archives, not cleaning up root jail.")
        elif os.path.ismount(os.path.join(CHROOT_DIR, "var", "lib", "apt", "lists")):
            print("[X] Failed to unmount /var/lib/apt/lists, not cleaning up root jail.")
        else:
            shutil.rmtree(CHROOT_DIR)

print(f"[✓] Build complete in {time.time() - delta:.2f} seconds! Output: {OUTPUT}")
sys.exit(0)