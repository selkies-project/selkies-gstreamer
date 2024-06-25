# Development and Contributions

This project was meant to be built upon community contributions from people without any prior media networking experience.

[GStreamer](https://gstreamer.freedesktop.org) is much easier to develop without prior experience on multimedia application development, and this project is a perfect starting point for anyone who wants to get started.

Please return your developments with a [Pull Request](https://github.com/selkies-project/selkies-gstreamer/pulls) if you made modifications to the code or added new features, especially if you use this project commercially (as per MPL-2.0 license obligations). We will be happy to help or consult if you are stuck.

**NOTE: this project is licensed under the [Mozilla Public License, version 2.0](https://www.mozilla.org/en-US/MPL/2.0/FAQ/), which obliges to share modified code files licensed by MPL-2.0 when distributed externally, but does not apply for any larger work outside this project, which might be open-source or proprietary under any license of choice. Externally originated components outside this project may contain works licensed over more restrictive copyleft/proprietary licenses, as well as other terms of intellectual property, including but not limited to patents, which users or developers are obliged to adhere to.**

Our license prevents proprietary entities from engulfing our code without providing anything back, unlike the Apache License, but does not impede any larger proprietary work embedding our code, unlike the GNU GPL/LGPL/AGPL. Either way, we strongly encourage proprietary entities to provide back your developments in terms of pull requests directly into our code repository.

As the relatively permissive license compared to similar projects is for the benefit of the community, non-profit or profit, please do not take advantage of it. If improvements are not merged into this code repository, it will ultimately lead to the project becoming unsustainable. We need your help to continue maintaining performance and quality, as well as staying competent compared to proprietary applications. We want commercial research and development to thrive together with Selkies-GStreamer.

## Contributions

Please join our [Discord](https://discord.gg/wDNGDeSW5F) server, then start out with the [Issues](https://github.com/selkies-project/selkies-gstreamer/issues) to see if new enhancements that you can make or things that you want solved have been already raised.

**No programming experience:** You can still be a tester or a community helper/moderator at [Discord](https://discord.gg/wDNGDeSW5F)! Do you see anything that feels uncomfortable compared to other projects? Raise an issue and suggest various improvements including to the documentation. Have you used OBS, FFmpeg, or any other live streaming/video editing software before? You can suggest optimized parameters for the video encoders from your experiences. You can experiment with various encoder parameters which are exposed in a very accessible way under [gstwebrtc_app.py](/src/selkies_gstreamer/gstwebrtc_app.py). You can add or modify properties exposed under the comment `ADD_ENCODER:` for each encoder, improving streaming performance.

**Some Python or HTML/JavaScript frontend experience:** Our codebase and web interface always has room for improvement. Consider helping out on various issues or cleaning up the code otherwise.

**Linux X11/Wayland/Container/Conda experience:** Please report issues with the capture interface and provide improvements for our reference containers. If you have the capacity to maintain conda-forge feedstocks, please add yourself as a maintainer and contribute new feedstocks. A protocol and interface can never be great without a great environment it runs in. If you want to bring Selkies-GStreamer to MacOSX or Windows, check our issues!

**C/Rust experience:** Selkies-GStreamer abstracts various media encoding and network capabilities behind GStreamer. We need you to fix bugs and implement new required elements in GStreamer or any other upstream dependencies. This will not only benefit Selkies-GStreamer but also help millions of other GStreamer users.

**Any type of multimedia networking experience:** While relevant experience is not necessary to contribute, we still feel great to have you as our companions. Please consider stepping up as a maintainer in addition to contributing! Development for commercial purposes are always fine as well as (our weak copyleft) license terms are complied with. Shape Selkies-GStreamer so that it fits your project as a first-class citizen, while keeping it accessible to many other people.

**WebRTC developers or Chromium/Firefox/Safari multimedia contributors:** We always need you, but you are generally very busy people. Even so, you can always provide directions on topics, ideas, specifications, or technologies that we have missed, so that other people including us can implement them. In many occasions, a single paragraph from experts are equal to hundreds of hours of work.

**Funding to improve this project:** If you want new features or improvements but if you are not a developer or lack enough time, please consider offering bounties by contacting us. If you want new features that currently are not yet available with [GStreamer](https://gstreamer.freedesktop.org), we must fund the small pool of full-time GStreamer developers capable of implementing new features to bring them into Selkies-GStreamer as well. Such issues are tagged as requiring upstream development. Even for features or improvements that are ready to be implemented, crowdfunding bounties motivate developers to solve them faster.

Regardless of your experience level, there is always something that you could help. Our code structure enables you to focus on parts of the code that you know best without necessarily understanding the rest.

When contributing, please follow the overall style of the code, and the names of all variables, classes, or functions should be unambiguous and as less generic/confusing as possible.

## Influenced Projects

Currently in collaboration and received influences from: <https://github.com/Xpra-org/xpra>, <https://github.com/m1k1o/neko>

Provided heavy influences to other projects: <https://github.com/nestriness/nestri>, <https://github.com/Steam-Headless/docker-steam-headless>, <https://github.com/ai-dock>

## Contributors

Contact information for contributors currently available for paid consulting tasks is available by request in [Discord](https://discord.gg/wDNGDeSW5F).

### Maintainers

These people make structural decisions for this project and press the `Merge Pull Request` button.

[Dan Isla](https://github.com/danisla): Project Founder, Owner, Industry Representative (ex-Google, ex-NASA, ex-itopia), Head Maintainer (Start - Sep 2023, July 2024 -), **currently available for paid consulting tasks**

[Seungmin Kim](https://github.com/ehfd): Co-Owner, Academia Representative (Yonsei University College of Medicine, San Diego Supercomputer Center), Head Maintainer (Apr 2022 - July 2024, est. 2025 -), currently not available for paid consulting tasks

### Code Contributors

[PMohanJ](https://github.com/PMohanJ): Contributed new features for the X11 input protocol as well as providing various fixes for the project overall and providing various means of analysis, **currently available for paid consulting tasks in tandem with senior maintainers**

[ayunami2000](https://github.com/ayunami2000): Provided various fixes for the WebRTC HTML5 web interface, as well as providing various means of analysis, **currently available for paid consulting tasks in tandem with senior maintainers**

[Carlos Ruiz](https://github.com/cruizba): [OpenVidu](https://openvidu.io) Team, provided various proposals for fixing the X11 input protocol

### Past Maintainers

[Jan Van Bruggen](https://github.com/JanCVanB): Project Co-Founder, ex-Google, ex-NASA, ex-itopia, current Verily

[Reisbel Machado](https://github.com/reisbel): itopia

# Knowledge Base

This section is a knowledge base for code contributions and development.

## Style Guide

- Shell scripts and Dockerfiles should use POSIX `sh` syntax as much as possible. Despite the shell scripts being run in `bash`, avoid using syntax only available in `bash` (such as `[[ ]]`), `zsh`, or other types of shells, unless absolutely needed.

- For Python, [Ruff](https://github.com/astral-sh/ruff) with Black formatting or [Black](https://github.com/psf/black) formatting are recommended. For JavaScript, HTML, CSS, Markdown, YAML, and other files, [Prettier](https://github.com/prettier/prettier) formatting is recommended. For code that is not already formatted in these formats, use the formatters with your Pull Requests if possible.

- There should be no empty lines with whitespaces, or line endings with whitespaces. Moreover, there should be a line break at the end of each code file unless the specific code file format should not have one. If there is not, it is okay, but include the line break with your Pull Requests if possible.

## Code Guide

- When editing certain parts of the codebase, they are very likely to interact with other components in a very different location, or the same content needs to be edited in multiple different locations. Therefore, commits or Pull Requests are very likely to corrupt the repository if you do not use search capabilities across the whole codebase as often as possible.

- Because of this, use the Visual Studio Code (or any other IDE of choice) **Search and Replace** capabilities rigorously (especially with fine-tuning through capitalization and regular expressions).

- However, the replacement capability, if without adequate care, may replace totally unrelated code. Take great care while using this capability, and reviewers must take special attention to detect potentially breaking typos which may arise from bulk replacement.

- Some code components have `CAPITALIZED_COMMENT:` comment sections such as `ADD_ENCODER:` or `OPUS_FRAME:`. These sections indicate that locations with the `CAPITALIZED_COMMENT:` need to be edited or added simultaneously.

## Container Guide

The [`docker-nvidia-glx-desktop`](https://github.com/selkies-project/docker-nvidia-glx-desktop) and [`docker-nvidia-egl-desktop`](https://github.com/selkies-project/docker-nvidia-egl-desktop) desktop container repositories and the [Example Container](/addons/example) share various components between each other:

`LICENSE`, `supervisord.conf`, `kasmvnc-entrypoint.sh`, and `selkies-gstreamer-entrypoint.sh` are always identical in both containers. As these components are also very similar to the [Example Container](/addons/example), it should be updated with both desktop containers.

The `Dockerfile` is always identical below and above the lines that say `Anything above/below this line should always be kept the same...`. This component is not shared with the [Example Container](/addons/example), and installation procedures for Selkies-GStreamer should be updated to the desktop containers on every release.

The `entrypoint.sh` components are always identical from the start until the line containing `export PULSE_SERVER=..."`. The script for installing NVIDIA userspace driver components are always identical except for the outermost `if` condition. Other script sections require manual assessment when updating.

`README.md` and `egl.yml`/`xgl.yml` files are similar but have different components, thus requiring manual assessment when updating.

## GStreamer Development Guide

GStreamer is based on GLib, which is an object-oriented programming interface on top of C (or C++/Rust). Therefore, many GStreamer objects inherit from other base objects, and object properties (configurations) are inherited from parent objects as well. Therefore, many object properties tend to be missing in the [Documentation Page](https://gstreamer.freedesktop.org/documentation/plugins_doc.html).

**NOTE: an easy and accurate way to identify GStreamer object properties is to use `gst-inspect-1.0 element_to_look`.** This will show all properties, including those of parent objects.

Otherwise, any [GStreamer](https://gstreamer.freedesktop.org) plugin [Documentation Page](https://gstreamer.freedesktop.org/documentation/plugins_doc.html) is supposed to have a **Hierarchy** section. As all GStreamer objects are defined as **classes** used with object-oriented programming, so any properties that you see in parent classes are also properties that you may use for your own classes and plugins.

Therefore, all contributors implementing or modifying code relevant to GStreamer are also to carefully check parent classes as well when configuring [properties](https://gstreamer.freedesktop.org/documentation/plugin-development/basics/args.html) or [capabilities](https://gstreamer.freedesktop.org/documentation/gstreamer/gstcaps.html).

Please also note that objects based on GstBin (most notably `webrtcbin` and `rtpbin`) may embed multiple sub-objects into a single object.
