**Go to [Knowledge Base](#knowledge-base) for information on customization.**

# Development and Contributions

**We are in need of maintainers and community contributors. Please consider stepping up, as we can never have too much help!**

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

[Dan Isla](https://github.com/danisla): Project Founder, Owner, Head Maintainer (Start - Sep 2023, August 2024 -), Industry Representative (ex-Google, ex-NASA, ex-itopia), **currently available for paid consulting tasks**

[Seungmin Kim](https://github.com/ehfd): Co-Owner, Head Maintainer (Apr 2022 - August 2024, est. 2025 -), Academia Representative (Yonsei University College of Medicine, San Diego Supercomputer Center), currently not available for paid consulting tasks (on hiatus from project)

[Dmitry Mishin](https://github.com/dimm0): Interim Head Maintainer (August 2024 -), Interim Academia Representative (University of California San Diego, San Diego Supercomputer Center)

### Code Contributors

[PMohanJ](https://github.com/PMohanJ): Contributed new features for the X11 input protocol as well as providing various fixes for the project overall and providing various means of analysis, **currently available for paid consulting tasks in tandem with senior maintainers**

[Kristian Ollikainen](https://github.com/DatCaptainHorse): Professional WebRTC and JavaScript frontend engineer, contributed various insights to the GStreamer and web components

[ayunami2000](https://github.com/ayunami2000): Provided various fixes for the WebRTC HTML5 web interface, as well as providing various means of analysis, **currently available for paid consulting tasks in tandem with senior maintainers**

[Carlos Ruiz](https://github.com/cruizba): [OpenVidu](https://openvidu.io) Team, provided various proposals for fixing the X11 input protocol

### Past Maintainers

[Jan Van Bruggen](https://github.com/JanCVanB): Project Co-Founder, ex-Google, ex-NASA, ex-itopia, current Verily

[Reisbel Machado](https://github.com/reisbel): itopia

# Knowledge Base

This section is a knowledge base for code contributions and development.

## Communities

- Selkies Discord: <https://discord.gg/wDNGDeSW5F>

- Selkies Matrix Space (Connect with United States HPC Academics, needs Matrix Account from <https://app.element.io>): <https://matrix.to/#/#ue4research:matrix.nrp-nautilus.io>

- Real-Time Streaming Discord (General WebRTC Advice): <https://discord.gg/KFS32mYXPr>

- GStreamer Matrix Space (Specific to GStreamer, needs Matrix Account from <https://app.element.io>): <https://matrix.to/#/#community:gstreamer.org>

## Resources

- **Our [Documentation](/docs/README.md) and [Issues](https://github.com/selkies-project/selkies-gstreamer/issues)/[Pull Requests](https://github.com/selkies-project/selkies-gstreamer/pulls)** (including closed Issues/Pull Requests) and <https://github.com/m1k1o/neko/issues/371>

- GStreamer Repository (sources of truth are below, other repositories such as `gst-plugins-base` have been relocated to the below):

<https://gitlab.freedesktop.org/gstreamer/gstreamer>

<https://gitlab.freedesktop.org/gstreamer/gst-plugins-rs>

<https://gitlab.freedesktop.org/gstreamer/meson-ports>

- GStreamer Documentation (`gst-inspect-1.0 module` tends to be much more accurate than this): <https://gstreamer.freedesktop.org/documentation/>

- WebRTC for the Curious: <https://webrtcforthecurious.com>

- WebRTC Official Google Groups: <https://groups.google.com/g/discuss-webrtc>

- Mozilla MDN: <https://developer.mozilla.org/en-US/docs/Web/API/WebRTC_API>

- WebRTC Hacks: <https://webrtchacks.com>

## Container Customization

**If you want to change the `Dockerfile`, you are recommended to use the original container as a base container and only replace the `entrypoint.sh` and `supervisord.conf` files. This will keep you up to date with the latest updates. Use persistent container tags (such as `v1.0.0-ubuntu24.04` for the [Example Container](component.md#example-container) or `24.04-20210101010101` for the desktop containers) to preserve a specific container build.**

Start with the below sample `Dockerfile` example and place your modified `entrypoint.sh` and `supervisord.conf` files within the same empty directory or Git repository (switch the `FROM` line to `ghcr.io/selkies-project/selkies-gstreamer/gst-py-example:main-ubuntu${DISTRIB_RELEASE}` for the [Example Container](component.md#example-container), and `ghcr.io/selkies-project/nvidia-glx-desktop:${DISTRIB_RELEASE}` or `ghcr.io/selkies-project/nvidia-egl-desktop:${DISTRIB_RELEASE}` for the desktop containers):

```dockerfile
ARG DISTRIB_RELEASE=24.04
FROM ghcr.io/selkies-project/nvidia-glx-desktop:${DISTRIB_RELEASE}
ARG DISTRIB_RELEASE

USER 0
# Restore file permissions to ubuntu user
RUN if [ -d "/usr/libexec/sudo" ]; then SUDO_LIB="/usr/libexec/sudo"; else SUDO_LIB="/usr/lib/sudo"; fi && \
    chown -R -f -h --no-preserve-root ubuntu:ubuntu /usr/bin/sudo-root /etc/sudo.conf /etc/sudoers /etc/sudoers.d /etc/sudo_logsrvd.conf "${SUDO_LIB}" || echo 'Failed to provide user permissions in some paths relevant to sudo'
USER 1000

# Use BUILDAH_FORMAT=docker in buildah
SHELL ["/usr/bin/fakeroot", "--", "/bin/sh", "-c"]
# Install and configure below this line

# Replace changed files
# Copy scripts and configurations used to start the container with `--chown=1000:1000`
#COPY --chown=1000:1000 entrypoint.sh /etc/entrypoint.sh
#RUN chmod -f 755 /etc/entrypoint.sh
#COPY --chown=1000:1000 selkies-gstreamer-entrypoint.sh /etc/selkies-gstreamer-entrypoint.sh
#RUN chmod -f 755 /etc/selkies-gstreamer-entrypoint.sh
#COPY --chown=1000:1000 kasmvnc-entrypoint.sh /etc/kasmvnc-entrypoint.sh
#RUN chmod -f 755 /etc/kasmvnc-entrypoint.sh
#COPY --chown=1000:1000 supervisord.conf /etc/supervisord.conf
#RUN chmod -f 755 /etc/supervisord.conf

SHELL ["/bin/sh", "-c"]

USER 0
# Enable sudo through sudo-root with uid 0
RUN if [ -d "/usr/libexec/sudo" ]; then SUDO_LIB="/usr/libexec/sudo"; else SUDO_LIB="/usr/lib/sudo"; fi && \
    chown -R -f -h --no-preserve-root root:root /usr/bin/sudo-root /etc/sudo.conf /etc/sudoers /etc/sudoers.d /etc/sudo_logsrvd.conf "${SUDO_LIB}" || echo 'Failed to provide root permissions in some paths relevant to sudo' && \
    chmod -f 4755 /usr/bin/sudo-root || echo 'Failed to set chmod setuid for root'

USER 1000
ENV SHELL=/bin/bash
ENV USER=ubuntu
ENV HOME=/home/ubuntu
WORKDIR /home/ubuntu

EXPOSE 8080

ENTRYPOINT ["/usr/bin/supervisord"]
```

## Container Guide

The [`docker-nvidia-glx-desktop`](https://github.com/selkies-project/docker-nvidia-glx-desktop)/[`docker-nvidia-egl-desktop`](https://github.com/selkies-project/docker-nvidia-egl-desktop) desktop container repositories (referenced as Desktop Containers here), and the [Example Container](/addons/example) share various components between each other:

`LICENSE`, `supervisord.conf`, `kasmvnc-entrypoint.sh`, and `selkies-gstreamer-entrypoint.sh` are always identical in both Desktop Containers (copy and paste between each container). As these components are also very similar to the [Example Container](/addons/example), **you need to do three Pull Requests including the [Example Container](/addons/example) if relevant lines changed in the [Example Container](/addons/example), and at least two Pull Requests for both Desktop Containers.**

The `Dockerfile` is always identical below and above the lines that say `Anything above/below this line should always be kept the same...` in both Desktop Containers. This component is not shared with the [Example Container](/addons/example), and installation procedures for Selkies-GStreamer should be updated to the desktop containers on every release, so **you need to do three Pull Requests including the [Example Container](/addons/example) if relevant lines changed in the [Example Container](/addons/example), and at least two Pull Requests for both Desktop Containers.**

The `entrypoint.sh` components are always identical from the start until the line containing `export PULSE_SERVER=..."` in both Desktop Containers. The script for installing NVIDIA userspace driver components are always identical except for the outermost `if` condition. Other script sections require manual assessment when updating, so **you need to do three Pull Requests including the [Example Container](/addons/example) if relevant lines changed in both Desktop Containers and the [Example Container](/addons/example).**

`README.md` and `egl.yml`/`xgl.yml` files in both Desktop Containers are similar but have different components, thus requiring manual assessment for both Desktop Containers when updating.

## Style Guide

- Shell scripts and Dockerfiles should use POSIX `sh` syntax as much as possible. Despite the shell scripts being run in `bash`, avoid using syntax only available in `bash` (such as `[[ ]]`), `zsh`, or other types of shells, unless absolutely needed. If non-POSIX syntax is used, prefer using `bash` syntax, but only if there are no equivalent POSIX alternatives.

- For Python, [Ruff](https://github.com/astral-sh/ruff) with Black formatting or [Black](https://github.com/psf/black) formatting are recommended. For JavaScript, HTML, CSS, Markdown, YAML, and other files, [Prettier](https://github.com/prettier/prettier) formatting is recommended. For code that is not already formatted in these formats, use the formatters with your Pull Requests if possible.

- There should be no empty lines with whitespaces, or line endings with whitespaces. Moreover, there should be a line break at the end of each code file unless the specific code file format should not have one. If there is not, it is okay, but include the line break with your Pull Requests if possible.

- Try using [`codespell`](https://github.com/codespell-project/codespell) or any other code spelling checker including the Visual Studio Code [Code Spell Checker](https://marketplace.visualstudio.com/items?itemName=streetsidesoftware.code-spell-checker), that can check spelling errors in the codebase before finalizing your pull request. Note that some fixes may be false positives, so please check the fixes manually (most notable false positives include `/dev/dri/renderD`).

## Code Guide

- **You need to understand the whole codebase fully before contributing developments.** When editing certain parts of the codebase, they are very likely to interact with other components in a very different location, or the same content needs to be edited in multiple different locations. Therefore, Commits or Pull Requests are very likely to corrupt the repository **UNLESS** you use rigorous search capabilities across the whole codebase as often as possible. Check previous commits as a starting point for the files that tend to be edited together.

- Because of this, use the Visual Studio Code (or any other IDE of choice) **Search and Replace** capabilities rigorously (especially with fine-tuning through case-sensitive search and regular expressions). However, the replacement capability, without adequate care, may replace totally unrelated code. Take great care while using this capability, and reviewers must take special attention to detect potentially breaking typos which may arise from Search and Replace.

- **Write or edit code in relevant files and reference them so that the code style is kept consistent.** For instance, many handler methods that start with `on_` are initially unset, then set and referenced in other components or classes during initialization. If you are implementing a new capability on certain methods or handlers that use methods starting with `on_` frequently, you have to create new `on_` methods as well to handle your capability. This assists with keeping the code highly readable, and putting methods or functions in the wrong files will harm the consistency of the code style. **If you are starting to feel that the location you are writing code in does not blend properly into adjacent code, you are probably writing it in the wrong place!**

- For example, assume that we are writing a new component that receives WebRTC Metrics from the web interface and writes them into multiple CSV files in the host ([#141](https://github.com/selkies-project/selkies-gstreamer/pull/141)). Because the WebRTC RTCDataChannel interface is used, receiving the metrics will be handled in [`webrtc_input.py`](/src/selkies_gstreamer/webrtc_input.py). But this does not mean that everything should be implemented in this file. Instead, they should be [implemented in the `Metrics` class](https://github.com/selkies-project/selkies-gstreamer/pull/141/commits/abae13645fdf0082f27041c59a14e1c030cf3763) of [`metrics.py`](/src/selkies_gstreamer/metrics.py), and be initialized in [`__main__.py`](/src/selkies_gstreamer/__main__.py). This way, relevant code stays in appropriate files and is initialized only when the capabilities are needed.

- Some code components have `CAPITALIZED_COMMENT:` comment sections such as `ADD_ENCODER:` or `OPUS_FRAME:`. These sections indicate that locations with the `CAPITALIZED_COMMENT:` must be edited or added simultaneously.

## GStreamer Development Guide

**Read [GStreamer Components](component.md#gstreamer-components) together with this guide.**

GStreamer is based on GLib, which is an object-oriented programming interface on top of C (or C++/Rust). Therefore, many GStreamer objects inherit from other base objects, and object properties (configurations) are inherited from parent objects as well. Therefore, many object properties tend to be missing in the [Documentation Page](https://gstreamer.freedesktop.org/documentation/plugins_doc.html).

**NOTE: an easy and accurate way to identify GStreamer object properties is to use `gst-inspect-1.0 element_to_look`.** This will show all properties, including those inherited from parent objects.

Otherwise, any [GStreamer](https://gstreamer.freedesktop.org) plugin [Documentation Page](https://gstreamer.freedesktop.org/documentation/plugins_doc.html) is supposed to have a **Hierarchy** section. As all GStreamer objects are defined as **classes** used with object-oriented programming, all properties that you see in parent classes are also properties that you may use for your own classes and plugins that inherit from the parent classes.

Therefore, all contributors implementing or modifying code relevant to GStreamer must also carefully check parent classes as well when configuring [Properties](https://gstreamer.freedesktop.org/documentation/plugin-development/basics/args.html) or [Capabilities](https://gstreamer.freedesktop.org/documentation/gstreamer/gstcaps.html).

Please also note that objects based on GstBin (most notably `webrtcbin` and `rtpbin`) may embed multiple sub-objects into a single object.

# Maintainer Documentation

- New releases are published by going to the [Publish release](https://github.com/selkies-project/selkies-gstreamer/actions/workflows/build_and_publish_release.yaml) GitHub Action Workflow, and triggering `workflow_dispatch` by clicking on `Run workflow` with `Branch: main`, and specifying the release tag. The draft release for the new proposed release will be generated in the [Releases](https://github.com/selkies-project/selkies-gstreamer/releases) page, only visible to the maintainers. After waiting for the release build to finish, editing the release notes, and publishing the release, the release will be visible as the latest release. **If the same release is created multiple times because of certain issues, make sure to delete the previous release and the tag before running the [Publish release](https://github.com/selkies-project/selkies-gstreamer/actions/workflows/build_and_publish_release.yaml) GitHub Action Workflow again.**
