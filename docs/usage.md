# Usage

## Locking the cursor and fullscreen mode

The cursor can be locked into the web interface using `Control + Shift + Left Click` in web browsers supporting the Pointer Lock API. Press `Escape` to exit this remote cursor mode. This remote cursor capability is useful for most games or graphics applications where the cursor must be confined to the remote screen. Fullscreen mode is available with the shortcut `Control + Shift + F`, or by pressing the fullscreen button in the configuration menu. Press `Escape` for a long time to exit fullscreen mode. The configuration menu is available by clicking the small button on the right of the interface with fullscreen turned off, or by using the shortcut `Control + Shift + M`.

## Command-line options and environment variables

Use `selkies-gstreamer --help` for all command-line options, after sourcing `gst-env`. Environment variables for command-line options are available as capitalizations of the options prepended by `SELKIES_` (such as `SELKIES_VIDEO_BITRATE` for `--video_bitrate`).

## Configuring Encoders, Display Capture, or Transport Protocols

[Components](component.md)
