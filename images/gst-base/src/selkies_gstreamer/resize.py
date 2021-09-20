import logging
import os
import re
import subprocess
from subprocess import Popen, PIPE, STDOUT

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

def resize_display(res):
    curr_res = res
    screen_name = "screen"
    resolutions = []

    screen_pat = re.compile(r'(.*)? connected.*?(\d+x\d+)\+.*')
    res_pat = re.compile(r'^(\d+x\d+)\s.*$')

    found_screen = False
    with os.popen('xrandr') as pipe:
        for line in pipe:
            screen_ma = re.match(screen_pat, line.strip())
            if screen_ma:
                found_screen = True
                screen_name, curr_res = screen_ma.groups()
            if found_screen:
                res_ma = re.match(res_pat, line.strip())
                if res_ma:
                    resolutions += res_ma.groups()

    if not found_screen:
        logger.error("failed to find screen info in xrandr output")
        return False

    w, h = [int(i) for i in res.split('x')]

    if screen_name.startswith("DVI"):
        # Set max resolution for hardware accelerator.
        max_res = "2560x1600"
    else:
        max_res = "4096x2160"

    max_w, max_h = [int(i) for i in max_res.split('x')]
    new_w, new_h = fit_res(w, h, max_w, max_h)
    new_res = "%dx%d" % (new_w, new_h)
    if res != new_res:
        logger.info("snapping resolution from %s to scaled max res (%s): %s" % (res, max_res, new_res))

        res = new_res
        w, h = new_w, new_h

    if curr_res == res:
        logger.info("target resolution is the same: %s, skipping resize" % res)
        return False

    logger.info("resizing display to %s" % res)
    if res not in resolutions:
        logger.info("adding mode %s to xrandr screen '%s'" % (res, screen_name))

        # Generate modeline, this works for Xvfb, not sure about xserver with nvidia driver
        modeline = "0.00 %s 0 0 0 %s 0 0 0 -hsync +vsync" % (w, h)

        # Create new mode from modeline
        logger.info("creating new xrandr mode: %s %s" % (res, modeline))
        cmd = ['xrandr', '--newmode', res, *re.split('\s+', modeline)]
        p = Popen(cmd, stdout=PIPE, stderr=PIPE)
        stdout, stderr = p.communicate()
        if p.returncode != 0:
            logger.error("failed to create new xrandr mode: '%s %s': %s%s" % (res, modeline, str(stdout), str(stderr)))
            return False

        # Add the mode to the screen.
        logger.info("adding xrandr mode '%s' to screen '%s'" % (res, screen_name))
        cmd = ['xrandr', '--addmode', screen_name, res]
        p = Popen(cmd, stdout=PIPE, stderr=PIPE)
        stdout, stderr = p.communicate()
        if p.returncode != 0:
            logger.error("failed to add mode '%s' using xrandr: %s%s" % (res, str(stdout), str(stderr)))
            return False

    # Apply the resolution change
    logger.info("applying xrandr mode: %s" % res)
    cmd = ['xrandr', '--output', screen_name, '--mode', res]
    p = Popen(cmd, stdout=PIPE, stderr=PIPE)
    stdout, stderr = p.communicate()
    if p.returncode != 0:
        logger.error("failed to apply xrandr mode '%s': %s%s" % (res, str(stdout), str(stderr)))
        return False

    return True

if __name__ == "__main__":
    import sys
    logging.basicConfig(level=logging.INFO)

    if len(sys.argv) < 2:
        print("USAGE: %s WxH" % sys.argv[0])
        sys.exit(1)
    res = sys.argv[1]

    resize_display(res)