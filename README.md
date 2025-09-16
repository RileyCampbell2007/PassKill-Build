# PassKill-Build
![License](https://img.shields.io/badge/License-BSD%203--Clause-blue.svg)

Build scripts for the PassKill live ISO

# Build instructions
_Building is only required if you are customizing the ISO yourself._

1. **Install dependencies**:
    
    Ubuntu/Debian

    ```bash
    sudo apt-get install debootstrap python3
    ```

    RHEL/Fedora

    ```bash
    sudo dnf install debootstrap python3
    ```
    *RHEL may need the Extra Packages for Enterprise Linux repository, install the `epel-release` package before installing debootstrap*

    Arch

    ```bash
    sudo pacman -S debootstrap python3
    ```

2. **Clone Build Repository**:

    ```bash
    git clone https://github.com/RileyCampbell2007/PassKill-Build.git
    cd PassKill-Build
    ```

3. **Build ISO**:

    ```bash
    sudo python3 build.py
    ```

    Build.py will put an ISO and an MD5 hash file into the `build` directory in the current directory by default.

# Advanced Configuration
The PassKill build system has a simple configuration system, any variables in config.py will overwrite those in build.py.

This is an example config.py that changes the volume ID of the ISO:
```python
ISO_VOLID="PassKill-Custom"
```

Or to change the package repository to use:
```python
MIRROR="your custom mirror"
```

These are the variables that build.py uses:

* `RELEASE_CODE_NAME` - The code name of the release to build off of. IE: `noble`, `plucky`
* `MIRROR` - The url of the repository mirror for apt and debootstrap to use.
* `CHROOT_DIR` - The location to create the temporary chroot environment.
* `IMAGE_DIR` - The location to store the temporary image files.
* `APT_CACHE` - The location to store the cached apt packages.
* `APT_LISTS` - The location to store the cached apt lists.
* `ISO_VOLID` - The volume ID of the resulting ISO.
* `OUTPUT` - The location of the resulting ISO. IE: `/tmp/passkill.iso`
* `MD5_OUTPUT` - The location of the resulting MD5 hash file. IE: `/tmp/passkill.md5`

