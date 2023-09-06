#!/bin/bash
set -e

function install_fluxbox() {
    sudo apt-get update
    sudo DEBIAN_FRONTEND=noninteractive apt-get install -y \
            fluxbox \
            terminator
}

function install_xfce() {
    sudo apt-get update
    sudo DEBIAN_FRONTEND=noninteractive apt-get install -y \
            xfce4 \
            xfce4-terminal \
            breeze-cursor-theme

    # Configure desktop environment
    sudo apt-get remove -y \
            xfce4-screensaver

    sudo ln -fs /etc/xfce4/defaults.list /usr/share/applications/defaults.list
}

function install_kde() {
    sudo apt-get update
    sudo DEBIAN_FRONTEND=noninteractive apt-get install -y \
            kde-plasma-desktop \
            konsole \
            breeze-cursor-theme
}

function install_ubuntu_desktop() {
    sudo apt-get update
    sudo DEBIAN_FRONTEND=noninteractive apt-get install -y \
            ubuntu-desktop \
            gnome-terminal \
            breeze-cursor-theme
}

case ${1,,} in
    fluxbox)
        install_fluxbox
        ;;
    xfce)
        install_xfce
        ;;
    kdeplasma)
        install_kde
        ;;
    ubuntu)
        install_ubuntu_desktop
        ;;
    *)
        echo "ERROR: unsupported desktop environment: $1"
        exit 1
        ;;
esac
