try:
    import sys
    import subprocess
    import os
    import traceback
    import requests
    import shutil
    import configparser
except ImportError as e:
    print(f"[X] Failed to load required module: {e}")
    try:
        sys.exit(1)
    except:
        exit(1)


APT_OPTIONS = ['-y','-o', 'Dpkg::Options::=--force-confold']

GENERIC_PACKAGES = ['ubuntu-standard', 'sudo', 'linux-image-6.14.0-27-generic'] # The kernel is pinned to 6.14.0-27-generic because 6.14.0-28 and 6.14.0-29 have a bug that makes it so losetup fails when trying to create a loopdev for a squashfs file on a read only file system.
LIVE_PACKAGES = ['casper', 'discover', 'laptop-detect', 'locales', 'mtools', 'binutils']
NETWORK_PACKAGES = ['network-manager', 'net-tools', 'iw']
BOOTLOADER_PACKAGES = ['grub-common','grub-gfxpayload-lists', 'grub-pc', 'grub-pc-bin', 'grub2-common', 'grub-efi-amd64-signed', 'shim-signed']
WINDOW_MANAGER = ['plymouth', 'plymouth-label', 'plymouth-theme-ubuntu-text', 'ubuntu-gnome-desktop', 'ubuntu-gnome-wallpapers']
TOOLS = ['gnome-disk-utility', 'gparted', 'udisks2', 'smartmontools', 'parted', 'gvfs-backends', 'gvfs-fuse', 'network-manager', 'network-manager-gnome', 'htop', 'iotop', 'ncdu', 'lsof', 'file', 'lshw', 'usbutils', 'clonezilla', 'testdisk', 'sleuthkit', 'binwalk', 'partimage', 'python3-hivex', 'python3-pip', 'firefox', 'git']
FILESYSTEMS = [
    # Core Linux/Unix
    "btrfs-progs", "xfsprogs", "f2fs-tools", "reiserfsprogs",
    "jfsutils", "nilfs-tools", "zfsutils-linux",

    # Windows and cross-platform
    "ntfs-3g", "dosfstools", "exfatprogs",
    "hfsprogs", "hfsutils", "udftools",

    # Network / Cluster FS
    "nfs-common", "cifs-utils", "sshfs",
    "glusterfs-client", "ceph-common",
    "davfs2", "fuse3",

    # Special / Archival / Misc
    "squashfs-tools", "erofs-utils",
    "mtd-utils", "fuseiso", "archivemount",
]


PACKAGES = GENERIC_PACKAGES + LIVE_PACKAGES + NETWORK_PACKAGES + BOOTLOADER_PACKAGES + WINDOW_MANAGER + TOOLS + FILESYSTEMS

BLOCKED_PACKAGES = ['libreoffice*', 'thunderbird*', 'rhythmbox*', 'gnome-mahjongg', 'gnome-mines', 'gnome-sudoku', 'aisleriot', 'cheese', 'simple-scan', 'transmission*', 'remmina*', 'totem*', 'shotwell*', 'hexchat*', 'deja-dup*', 'ubuntu-docs', 'gnome-user-docs', 'snapd', 'plymouth-themes', 'plymouth-theme', 'plymouth-theme-spinner']


print('[CHROOT] Setting up chroot...')
try:
    os.makedirs('/proc', exist_ok=True)
    os.makedirs('/sys', exist_ok=True)
    os.makedirs('/dev/pts', exist_ok=True)
    subprocess.run(['mount', 'none', '-t', 'proc', '/proc'], check=True)
    subprocess.run(['mount', 'none', '-t', 'sysfs', '/sys'], check=True)
    subprocess.run(['mount', 'none', '-t', 'devpts', '/dev/pts'], check=True)

    os.environ['HOME'] = '/root'
    os.environ['LC_ALL'] = 'C'
    os.environ['DEBIAN_FRONTEND'] = 'noninteractive'

    open('/etc/casper.conf', 'w').write("""
export USERNAME="passkill"
export USERFULLNAME="PassKill live session user"
export HOST="passkill"
export BUILD_SYSTEM="Ubuntu"
export FLAVOUR="PassKill"
""".strip())
    

    print('[CHROOT] Updating package list...')
    try:
        subprocess.run(['apt-get', 'update'], check=True)
    except Exception as e:
        traceback.print_exc()
        print("[CHROOT X] Failed to update package list.")
        sys.exit(1)

    
    print('[CHROOT] Installing software-properties-common...')
    try:
        subprocess.run(['apt-get', 'install', 'software-properties-common']+APT_OPTIONS, check=True)
    except Exception as e:
        traceback.print_exc()
        print("[CHROOT X] Failed to install software-properties-common.")
        sys.exit(1)

    
    print('[CHROOT] Blocking unwanted packages...')
    try:
        os.makedirs('/etc/apt/preferences.d', exist_ok=True)
        open('/etc/apt/preferences.d/99-blacklist', 'w').write(f"""
Package: {' '.join(BLOCKED_PACKAGES)}
Pin: release *
Pin-Priority: -1
""".strip())
    except Exception as e:
        traceback.print_exc()
        print("[CHROOT X] Failed to block unwanted packages.")
        sys.exit(1)


    print('[CHROOT] Setting up Mozilla repo...')
    try:
        os.makedirs('/etc/apt/preferences.d', exist_ok=True)
        subprocess.run(['add-apt-repository', 'ppa:mozillateam/ppa', '-y'], check=True)
        open('/etc/apt/preferences.d/mozilla-firefox', 'w').write("""
Package: firefox*
Pin: release o=LP-PPA-mozillateam
Pin-Priority: 501
""".strip())
    except Exception as e:
        traceback.print_exc()
        print("[CHROOT X] Failed to set up Mozilla repo.")
        sys.exit(1)


    print('[CHROOT] Updating package list...')
    try:
        subprocess.run(['apt-get', 'update'], check=True)
    except Exception as e:
        traceback.print_exc()
        print("[CHROOT X] Failed to update package list.")
        sys.exit(1)


    print('[CHROOT] Installing systemd...')
    try:
        subprocess.run(['apt-get', 'install', 'libterm-readline-gnu-perl', 'systemd-sysv', 'dbus-bin']+APT_OPTIONS, check=True)
    except Exception as e:
        traceback.print_exc()
        print("[CHROOT X] Failed to install systemd.")
        sys.exit(1)


    print('[CHROOT] Setting up machine-id and divert...')
    try:
        dbusProc = subprocess.run(['dbus-uuidgen'], check=True, stdout=subprocess.PIPE, text=True)
        open('/etc/machine-id', 'w').write(dbusProc.stdout)
        subprocess.run(['ln', '-fs', '/etc/machine-id', '/var/lib/dbus/machine-id'], check=True)
        subprocess.run(['dpkg-divert', '--local', '--rename', '--add', '/sbin/initctl'], check=True)
        subprocess.run(['ln', '-s', '/bin/true', '/sbin/initctl'], check=True)


        print('[CHROOT] Updating packages...')
        try:
            subprocess.run(['apt-get', 'dist-upgrade']+APT_OPTIONS, check=True)
        except Exception as e:
            traceback.print_exc()
            print("[CHROOT X] Failed to update packages.")
            sys.exit(1)


        print('[CHROOT] Installing packages...')
        try:
            subprocess.run(['apt-get', 'install']+APT_OPTIONS+PACKAGES, check=True)
        except Exception as e:
            traceback.print_exc()
            print("[CHROOT X] Failed to install packages.")
            sys.exit(1)


        print('[CHROOT] Cleaning up packages...')
        try:
            subprocess.run(['apt-get', 'autoremove', '-y', '--purge'], check=True)
        except Exception as e:
            traceback.print_exc()
            print("[CHROOT X] Failed to clean up packages.")
            sys.exit(1)
        

        print('[CHROOT] Unblocking unwanted packages...')
        try:
            if os.path.exists('/etc/apt/preferences.d/99-blacklist'):
                os.remove('/etc/apt/preferences.d/99-blacklist')
        except Exception as e:
            traceback.print_exc()
            print("[CHROOT X] Failed to unblock unwanted packages.")
            sys.exit(1)


        print('[CHROOT] Building ntfs-3g-system-compression...')
        try:
            BUILD_DEPS = ['autoconf', 'automake', 'libtool', 'pkg-config', 'ntfs-3g-dev', 'libfuse-dev', 'build-essential']

            installed_packages = subprocess.run(['dpkg-query', '-W', '-f=${binary:Package}\n'], check=True, stdout=subprocess.PIPE, text=True).stdout.splitlines()
            for package in installed_packages:
                if package in BUILD_DEPS:
                    BUILD_DEPS.remove(package)

            subprocess.run(['apt-get', 'install']+BUILD_DEPS+APT_OPTIONS, check=True)

            subprocess.run(['git', 'clone', 'https://github.com/ebiggers/ntfs-3g-system-compression.git', '/ntfs-3g-system-compression'], check=True)
            subprocess.run(['autoreconf', '-i'], check=True, cwd='/ntfs-3g-system-compression')
            subprocess.run(['chmod', '+x', '/ntfs-3g-system-compression/configure'], check=True)
            subprocess.run(['/ntfs-3g-system-compression/configure'], check=True, cwd='/ntfs-3g-system-compression')
            subprocess.run(['make'], check=True, cwd='/ntfs-3g-system-compression')

            result = subprocess.run(["ntfs-3g", "-h"], capture_output=True, text=True)

            plugin_path = None
            for line in result.stderr.splitlines() + result.stdout.splitlines():
                if line.startswith("Plugin path: "):
                    plugin_path = line.split(":", 1)[1].strip()
                    break

            for root, dirs, files in os.walk("/ntfs-3g-system-compression"):
                for file in files:
                    if file == "ntfs-plugin-80000017.so":
                        plugin = os.path.join(root, file)

            os.makedirs(plugin_path, exist_ok=True)
            subprocess.run(['cp', plugin, os.path.join(plugin_path, 'ntfs-plugin-80000017.so')], check=True)

            subprocess.run(['apt-get', 'purge']+BUILD_DEPS+APT_OPTIONS, check=True)
            subprocess.run(['apt-get', 'autoremove', '-y', '--purge'], check=True)
            shutil.rmtree('/ntfs-3g-system-compression')
        except Exception as e:
            traceback.print_exc()
            print("[CHROOT X] Failed to build ntfs-3g-system-compression.")
            sys.exit(1)


        print('[CHROOT] Setting up plymouth...')
        try:
            subprocess.run(['update-alternatives', '--install', '/usr/share/plymouth/themes/default.plymouth', 'default.plymouth', '/usr/share/plymouth/themes/passkill/passkill.plymouth', '10'], check=True)
            subprocess.run(['update-alternatives', '--set', 'default.plymouth', '/usr/share/plymouth/themes/passkill/passkill.plymouth'], check=True)
        except Exception as e:
            traceback.print_exc()
            print("[CHROOT X] Failed to set up plymouth.")
            sys.exit(1)


        print('[CHROOT] Setting sidebar apps and theme...')
        try:
            gschema = configparser.ConfigParser()
            gschema.read('/usr/share/glib-2.0/schemas/10_ubuntu-settings.gschema.override')

            favoriteApps = "['firefox.desktop', 'org.gnome.Nautilus.desktop', 'org.gnome.Terminal.desktop', 'org.gnome.DiskUtility.desktop', 'gparted.desktop']"

            gschema['org.gnome.shell']['favorite-apps'] = favoriteApps
            gschema['org.gnome.desktop.interface']['gtk-theme'] = '"Yaru-dark"'
            gschema['org.gnome.desktop.interface']['icon-theme'] = '"Yaru-dark"'
            gschema['org.gnome.desktop.interface:GNOME-Greeter']['gtk-theme'] = '"Yaru-dark"'
            gschema['org.gnome.desktop.interface:GNOME-Greeter']['icon-theme'] = '"Yaru-dark"'
            gschema['org.gnome.shell:ubuntu']['favorite-apps'] = favoriteApps
            gschema['org.gnome.desktop.interface:ubuntu']['gtk-theme'] = '"Yaru-dark"'
            gschema['org.gnome.desktop.interface:ubuntu']['icon-theme'] = '"Yaru-dark"'

            gschema.write(open('/usr/share/glib-2.0/schemas/10_ubuntu-settings.gschema.override', 'w'))

            os.makedirs('/etc/dconf/profile', exist_ok=True)
            os.makedirs('/etc/dconf/db/local.d', exist_ok=True)
            
            open('/etc/dconf/profile/user', 'w').write("""
user-db:user
system-db:local
""".strip())
            open('/etc/dconf/db/local.d/00-passkill','w').write("""
[org/gnome/desktop/interface]
gtk-theme='Yaru-dark'
icon-theme='Yaru-dark'
color-scheme='prefer-dark'

[org/gnome/shell]
favorite-apps=['firefox.desktop','org.gnome.Nautilus.desktop','org.gnome.Terminal.desktop','org.gnome.DiskUtility.desktop','gparted.desktop']
""".strip())
        except Exception as e:
            traceback.print_exc()
            print("[CHROOT X] Failed to set sidebar apps and theme.")
            sys.exit(1)


        print('[CHROOT] Setting power settings...')
        try:
            open('/usr/share/glib-2.0/schemas/99_passkill-power-settings.gschema.override', 'w').write("""
[org.gnome.desktop.session]
# Set idle-delay to 0 to disable screen blanking due to inactivity
idle-delay=uint32 0

[org.gnome.settings-daemon.plugins.power]
# Disable automatic suspend when on battery power
sleep-inactive-battery-type='nothing'
# Disable automatic suspend when on AC power
sleep-inactive-ac-type='nothing'
# Set suspend timeouts to 0 (effectively disabled, reinforces the type setting)
sleep-inactive-battery-timeout=0
sleep-inactive-ac-timeout=0
""".strip())
        except Exception as e:
            traceback.print_exc()
            print("[CHROOT X] Failed to set power settings.")
            sys.exit(1)


        print('[CHROOT] Recompiling GSettings schemas...')
        try:
            subprocess.run(['glib-compile-schemas', '/usr/share/glib-2.0/schemas'], check=True)
        except Exception as e:
            traceback.print_exc()
            print("[CHROOT X] Failed to compile GSettings schemas.")
            sys.exit(1)


        print('[CHROOT] Recompiling dconf...')
        try:
            subprocess.run(['dconf', 'update'], check=True)
        except Exception as e:
            traceback.print_exc()
            print("[CHROOT X] Failed to compile dconf.")
            sys.exit(1)

        
        print('[CHROOT] Configuring NetworkManager...')
        try:
            open('/etc/NetworkManager/NetworkManager.conf', 'w').write("""
[main]
plugins=ifupdown,keyfile
dns=systemd-resolved

[ifupdown]
managed=false
""".strip())
            
            open('/etc/NetworkManager/conf.d/10-globally-managed-devices.conf', 'w').write("")
            subprocess.run(['dpkg-reconfigure', 'network-manager'], check=True)
        except Exception as e:
            traceback.print_exc()
            print("[CHROOT X] Failed to configure NetworkManager.")
            sys.exit(1)


        print('[CHROOT] Updating initramfs...')
        try:
            subprocess.run(['update-initramfs', '-u'], check=True)
        except Exception as e:
            traceback.print_exc()
            print("[CHROOT X] Failed to update initramfs.")
            sys.exit(1)
        

        print('[CHROOT] Building image files...')
        try:
            os.makedirs('/image/casper', exist_ok=True)
            os.makedirs('/image/isolinux', exist_ok=True)
            os.makedirs('/image/install', exist_ok=True)

            subprocess.run(['/bin/bash', '-c', 'cp /boot/vmlinuz-*-generic /image/casper/vmlinuz'], check=True)
            subprocess.run(['/bin/bash', '-c', 'cp /boot/initrd.img-*-generic /image/casper/initrd'], check=True)

            memtestUrl = 'https://memtest.org/download/v7.00/mt86plus_7.00.binaries.zip'
            memtestZip = requests.get(memtestUrl)
            open('/image/install/memtest86.zip', 'wb').write(memtestZip.content)
            open('/image/install/memtest86+.bin', 'wb').write(subprocess.run(['unzip', '-p', '/image/install/memtest86.zip', 'memtest64.bin'], check=True, stdout=subprocess.PIPE).stdout)
            open('/image/install/memtest86+.efi', 'wb').write(subprocess.run(['unzip', '-p', '/image/install/memtest86.zip', 'memtest64.efi'], check=True, stdout=subprocess.PIPE).stdout)
            os.remove('/image/install/memtest86.zip')

            open('/image/ubuntu', 'w').write("")

            open('/image/isolinux/grub.cfg', 'w').write("""
search --set=root --file /ubuntu

insmod all_video

loadfont unicode

set menu_color_normal=white/black
set menu_color_highlight=black/light-gray

set default="0"
set timeout=30

menuentry "Launch PassKill" {
    set gfxpayload=keep
    linux /casper/vmlinuz boot=casper nopersistent quiet splash ---
    initrd /casper/initrd
}

menuentry "Launch PassKill to RAM" {
    set gfxpayload=keep
    linux /casper/vmlinuz boot=casper nopersistent quiet splash toram ---
    initrd /casper/initrd
}

menuentry "Launch PassKill (Safe Graphics)" {
    set gfxpayload=keep
    linux /casper/vmlinuz boot=casper nopersistent quiet splash nomodeset ---
    initrd /casper/initrd
}

menuentry "Launch PassKill to RAM (Safe Graphics)" {
    set gfxpayload=keep
    linux /casper/vmlinuz boot=casper nopersistent quiet splash nomodeset toram ---
    initrd /casper/initrd
}

grub_platform
if [ "$grub_platform" = "efi" ]; then
    menuentry "Test memory Memtest86+" {
        linux /install/memtest86+.efi
    }

    menuentry 'UEFI Firmware Settings' {
        fwsetup
    }
else
    menuentry "Test memory Memtest86+" {
        linux16 /install/memtest86+.bin
    }
fi

menuentry 'Boot from next volume' {
    exit 1
}
""".strip())
            
            open('/image/README.diskdefines', 'w').write("""
    #define DISKNAME  PassKill
    #define TYPE  binary
    #define TYPEbinary  1
    #define ARCH  amd64
    #define ARCHamd64  1
    #define DISKNUM  1
    #define DISKNUM1  1
    #define TOTALNUM  0
    #define TOTALNUM0  1
    """.strip())
        except Exception as e:
            traceback.print_exc()
            print("[CHROOT X] Failed to build image files.")
            sys.exit(1)


        print('[CHROOT] Creating image...')
        try:
            subprocess.run(['cp', '/usr/lib/shim/shimx64.efi.signed.previous', '/image/isolinux/bootx64.efi'], check=True)
            subprocess.run(['cp', '/usr/lib/shim/mmx64.efi', '/image/isolinux/mmx64.efi'], check=True)
            subprocess.run(['cp', '/usr/lib/grub/x86_64-efi-signed/grubx64.efi.signed', '/image/isolinux/grubx64.efi'], check=True)

            open('/image/isolinux/efiboot.img', 'wb').write(b"\x00"*10485760)
            subprocess.run(['mkfs.vfat', '-F', '16', '/image/isolinux/efiboot.img'], check=True)
            environ = os.environ.copy()
            environ['LC_CTYPE']='C'
            subprocess.run(['mmd', '-i', 'efiboot.img', 'efi', 'efi/ubuntu', 'efi/boot'], check=True, env=environ, cwd='/image/isolinux/')
            subprocess.run(['mcopy', '-i', 'efiboot.img', './bootx64.efi', '::efi/boot/bootx64.efi'], check=True, env=environ, cwd='/image/isolinux/')
            subprocess.run(['mcopy', '-i', 'efiboot.img', './mmx64.efi', '::efi/boot/mmx64.efi'], check=True, env=environ, cwd='/image/isolinux/')
            subprocess.run(['mcopy', '-i', 'efiboot.img', './grubx64.efi', '::efi/boot/grubx64.efi'], check=True, env=environ, cwd='/image/isolinux/')
            subprocess.run(['mcopy', '-i', 'efiboot.img', './grub.cfg', '::efi/ubuntu/grub.cfg'], check=True, env=environ, cwd='/image/isolinux/')

            subprocess.run([
                "grub-mkstandalone",
                    "--format=i386-pc",
                    "--output=/image/isolinux/core.img",
                    '--install-modules=linux16 linux normal iso9660 biosdisk memdisk search tar ls',
                    '--modules=linux16 linux normal iso9660 biosdisk search',
                    '--locales=',
                    '--fonts=',
                    'boot/grub/grub.cfg=/image/isolinux/grub.cfg',
            ], check=True)

            with open('/image/isolinux/bios.img', 'wb') as f:
                f.write(open('/usr/lib/grub/i386-pc/cdboot.img', 'rb').read())
                f.write(open('/image/isolinux/core.img', 'rb').read())
            
            subprocess.run(['/bin/bash', '-c', "(find /image -type f -print0 | xargs -0 md5sum | grep -v -e '/image/isolinux' > /image/md5sum.txt)"], check=True)
        except Exception as e:
            traceback.print_exc()
            print("[CHROOT X] Failed to create image.")
            sys.exit(1)


    except Exception as e:
        traceback.print_exc()
        print("[CHROOT X] Failed to set up machine-id and divert.")
        sys.exit(1)
    
    finally:
        print('[CHROOT] Removing divert...')
        open('/etc/machine-id', 'w').write("")
        if os.path.exists('/sbin/initctl'):
            os.remove('/sbin/initctl')
        subprocess.run(['dpkg-divert', '--rename', '--remove', '/sbin/initctl'], check=False)
        shutil.rmtree('/tmp', ignore_errors=True)
        os.mkdir('/tmp', 0o1777)
        if os.path.exists('/root/.bash_history'):
            os.remove('/root/.bash_history')

        
except Exception as e:
    traceback.print_exc()
    print("[CHROOT X] Unknown failure.")
    sys.exit(1)

finally:
    print("[CHROOT] Cleaning up...")
    subprocess.run(['umount', '/proc'], check=False)
    subprocess.run(['umount', '/sys'], check=False)
    subprocess.run(['umount', '/dev/pts'], check=False)