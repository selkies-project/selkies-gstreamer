# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

import asyncio
import logging
import os
import re
import subprocess
from shutil import which

logger = logging.getLogger("gstwebrtc_app_resize")
logger.setLevel(logging.DEBUG)

def fit_res(w, h, max_w, max_h):
    if w < max_w and h < max_h:
        # Input resolution fits
        return w, h

    # Reduce input dimensions until they fit
    new_w = float(w)
    new_h = float(h)
    while new_w > max_w or new_h > max_h:
        new_w = float(new_w * 0.9999)
        new_h = float(new_h * 0.9999)

    # Snap final resolution to be divisible by 2.
    new_w, new_h = [int(i) + int(i)%2 for i in (new_w, new_h)]
    return new_w, new_h

def get_new_res(res):
    screen_name = "screen"
    resolutions = []

    screen_pat = re.compile(r'(.*)? connected.*?')
    current_pat = re.compile(r'.*current (\d+ x \d+).*')
    res_pat = re.compile(r'^(\d+x\d+)\s.*$')

    found_screen = False
    curr_res = new_res = max_res = res
    with os.popen('xrandr') as pipe:
        for line in pipe:
            screen_ma = re.match(screen_pat, line.strip())
            current_ma = re.match(current_pat, line.strip())
            if screen_ma:
                found_screen = True
                screen_name, = screen_ma.groups()
            if current_ma:
                curr_res, = current_ma.groups()
                curr_res = curr_res.replace(" ", "")
            if found_screen:
                res_ma = re.match(res_pat, line.strip())
                if res_ma:
                    resolutions += res_ma.groups()

    if not found_screen:
        logger.error("failed to find screen info in xrandr output")
        return curr_res, new_res, resolutions, max_res

    w, h = [int(i) for i in res.split('x')]

    if screen_name.startswith("DVI"):
        # Set max resolution for hardware accelerator.
        max_res = "2560x1600"
    else:
        max_res = "7680x4320"

    max_w, max_h = [int(i) for i in max_res.split('x')]
    new_w, new_h = fit_res(w, h, max_w, max_h)
    new_res = "%dx%d" % (new_w, new_h)

    resolutions.sort()
    return curr_res, new_res, resolutions, max_res, screen_name

def resize_display(res):
    curr_res, new_res, resolutions, max_res, screen_name = get_new_res(res)
    if curr_res == new_res:
        logger.info("target resolution is the same: %s, skipping resize" % res)
        return False

    w, h = new_res.split("x")
    res = mode = new_res

    logger.info("resizing display to %s" % res)
    if res not in resolutions:
        logger.info("adding mode %s to xrandr screen '%s'" % (res, screen_name))

        mode, modeline = generate_xrandr_gtf_modeline(res)

        # Create new mode from modeline
        logger.info("creating new xrandr mode: %s %s" % (mode, modeline))
        cmd = ['xrandr', '--newmode', mode, *re.split('\s+', modeline)]
        p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, stderr = p.communicate()
        if p.returncode != 0:
            logger.error("failed to create new xrandr mode: '%s %s': %s%s" % (mode, modeline, str(stdout), str(stderr)))
            return False

        # Add the mode to the screen.
        logger.info("adding xrandr mode '%s' to screen '%s'" % (mode, screen_name))
        cmd = ['xrandr', '--addmode', screen_name, mode]
        p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, stderr = p.communicate()
        if p.returncode != 0:
            logger.error("failed to add mode '%s' using xrandr: %s%s" % (mode, str(stdout), str(stderr)))
            return False

    # Apply the resolution change
    logger.info("applying xrandr screen '%s' mode: %s" % (screen_name, mode))
    cmd = ['xrandr', '--output', screen_name, '--mode', mode]
    p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout, stderr = p.communicate()
    if p.returncode != 0:
        logger.error("failed to apply xrandr mode '%s': %s%s" % (mode, str(stdout), str(stderr)))
        return False

    return True

def generate_xrandr_gtf_modeline(res):
    mode = ""
    modeline = ""
    modeline_pat = re.compile(r'^.*Modeline\s+"(.*?)"\s+(.*)')
    if len(res.split("x")) == 2:
        # have WxH format
        toks = res.split("x")
        gtf_res = "{} {} 60".format(toks[0], toks[1])
        mode = res
    elif len(res.split(" ")) == 2:
        # have W H format
        toks = res.split(" ")
        gtf_res = "{} {} 60".format(toks[0], toks[1])
        mode = "{}x{}".format(toks[0], toks[1])
    elif len(res.split(" ")) == 3:
        # have W H refresh format
        toks = res.split(" ")
        gtf_res = res
        mode = "{}x{}".format(toks[0], toks[1])
    else:
        raise Exception("unsupported input resolution format: {}".format(res))

    with os.popen('cvt -r ' + gtf_res) as pipe:
        for line in pipe:
            modeline_ma = re.match(modeline_pat, line.strip())
            if modeline_ma:
                _, modeline = modeline_ma.groups()
    return mode, modeline

def set_dpi(dpi):
    if which("xfconf-query"):
        # Set window scale
        cmd = ["xfconf-query", "-c", "xsettings", "-p", "/Xft/DPI", "-s", str(dpi), "--create", "-t", "int"]
        p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, stderr = p.communicate()
        if p.returncode != 0:
            logger.error("failed to set XFCE DPI to: '%d': %s%s" % (dpi, str(stdout), str(stderr)))
            return False
    else:
        logger.warning("failed to find supported window manager to set DPI.")
        return False

    return True

def set_cursor_size(size):
    if which("xfconf-query"):
        # Set cursor size
        cmd = ["xfconf-query", "-c", "xsettings", "-p", "/Gtk/CursorThemeSize", "-s", str(size), "--create", "-t", "int"]
        p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, stderr = p.communicate()
        if p.returncode != 0:
            logger.error("failed to set XFCE cursor size to: '%d': %s%s" % (size, str(stdout), str(stderr)))
            return False
    else:
        logger.warning("failed to find supported window manager to set DPI.")
        return False

    return True

async def main():
    import sys
    logging.basicConfig(level=logging.INFO)

    if len(sys.argv) < 2:
        print("USAGE: %s WxH" % sys.argv[0])
        sys.exit(1)
    res = sys.argv[1]
    print(await asyncio.to_thread(resize_display, res))

def entrypoint():
    asyncio.run(main())

if __name__ == "__main__":
    entrypoint()
