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

If GStreamer is installed at a certain location, set its path to the environment variable $GSTREAMER_PATH, then make sure your environment is set correctly using the below commands:

export PATH=${GSTREAMER_PATH}/bin:${PATH}
export LD_LIBRARY_PATH=${GSTREAMER_PATH}/lib/x86_64-linux-gnu:${LD_LIBRARY_PATH}
export GI_TYPELIB_PATH=${GSTREAMER_PATH}/lib/x86_64-linux-gnu/girepository-1.0:/usr/lib/x86_64-linux-gnu/girepository-1.0:${GI_TYPELIB_PATH}
GST_PY_PATH=$(find ${GSTREAMER_PATH}/lib -type d -name "python3.*")
export PYTHONPATH=${GST_PY_PATH}/site-packages:${GSTREAMER_PATH}/lib/python3/dist-packages:${PYTHONPATH}
        """
        print(msg)
        sys.exit(1)
