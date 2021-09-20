import sys

# import gi and Gst test
try:
    import gstwebrtc_app
    print("gst-python: import gi test PASSED")
except Exception as e:
    print("gst-python: import gi test FAILED")
    sys.exit(1)

# gi repository test
import gi
gi.require_version("Gst", "1.0")
from gi.repository import Gst
try:
    res = Gst.Fraction(60, 1)
    if res:
        print("gst-python: Gst.Fraction test PASSED")
except Exception as e:
    print("gst-python: Gst.Fraction test FAILED: %s" % e)
    sys.exit(1)

# nvcodec test
try:
    app = gstwebrtc_app.GSTWebRTCApp(encoder="nvh264enc")
    if app:
        print("gst-python: gst plugin check PASSED")
except Exception as e:
    print("gst-python: plugin check FAILED: %s" % e)
    sys.exit(1)