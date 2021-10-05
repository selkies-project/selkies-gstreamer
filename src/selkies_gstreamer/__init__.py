import os
import sys
import time
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Verify gstreamer installation
retry = True
while retry:
    try:
        import gi
        gi.require_version("Gst", "1.0")
        gi.require_version('GstWebRTC', '1.0')
        gi.require_version('GstSdp', '1.0')
        from gi.repository import Gst

        Gst.init(None)
        f = Gst.Fraction(60/1)
        print("INFO: gst-python install looks OK")
        break
    except Exception as e:
        msg = """
ERROR: could not find working gst-python installation.

If gstreamer is installed at /opt/gstreamer, then make sure your environment is set correctly:

export PATH=/opt/gstreamer/bin:${PATH}
export LD_LIBRARY_PATH=/opt/gstreamer/lib/x86_64-linux-gnu
export GI_TYPELIB_PATH=/opt/gstreamer/lib/x86_64-linux-gnu/girepository-1.0:/usr/lib/x86_64-linux-gnu/girepository-1.0
export PYTHONPATH=/opt/gstreamer/lib/python3.8/site-packages:/opt/gstreamer/lib/python3/dist-packages:${PYTHONPATH}
        """
        print(msg)
        sys.exit(1)
