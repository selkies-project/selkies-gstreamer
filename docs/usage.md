# Usage

## Shortcuts

**Fullscreen: `Control + Shift + F` or Fullscreen Button**

**Remote (Game) Cursor Lock: `Ctrl + Shift + LeftClick`**

**Open Side Menu: Ctrl + Shift + M or Side Button**

Fullscreen mode is available with the shortcut `Control + Shift + F`, or by pressing the fullscreen button in the configuration menu. Press `Escape` for at least two seconds to exit fullscreen mode.

The cursor can be locked into the web interface using `Control + Shift + Left Click` in web browsers supporting the Pointer Lock API. Press `Escape` to exit this remote cursor mode. This remote cursor capability is useful for most games or graphics applications where the cursor must be confined to the remote screen.

The configuration menu is available by clicking the small button on the right side of the interface with the fullscreen turned off, or by using the shortcut `Control + Shift + M`.

## Command-Line Options and Environment Variables

Use `selkies-gstreamer --help` for all command-line options, after the source command `. ./gst-env` for compiled GStreamer or the source command `. ./bin/activate` for Conda.

Environment variables for command-line options are available as capitalizations of the options prepended by `SELKIES_` (such as `SELKIES_VIDEO_BITRATE` for `--video_bitrate`).

## Configuring Encoders, Display Capture, or Transport Protocols

[Components](component.md#gstreamer-components)

## CI/CD Build

We use Docker® containers for building every commit. The root directory [`Dockerfile`](https://github.com/selkies-project/selkies-gstreamer/tree/main/Dockerfile) and Dockerfiles within the [`addons`](https://github.com/selkies-project/selkies-gstreamer/tree/main/addons) directory provide directions for building each component, so that you may replicate the procedures in your own setup even without Docker® by copying the commands to your own shell.
