# Development

This project was meant to be built upon community contributions. [GStreamer](https://gstreamer.freedesktop.org) is much easier to develop without prior experience on multimedia application development, and this project is a perfect starting point for anyone who wants to get started. Please give back with a [Pull Request](https://github.com/selkies-project/selkies-gstreamer/pulls) if you made modifications to the code or added new features, especially if you use this project commercially. We will be happy to help if you are stuck.

Regardless of whether you are an experienced developer or engineer already with experience on media pipelines, internet standards, video conferencing applications using SIP or H.323, or all other multimedia projects, just getting started on multimedia development, or even getting started on Python, JavaScript, or HTML, there can be something that you may help. Our code structure enables you to focus on parts of the code that you know best without necessarily understanding the rest.

Even if you are not a developer, you still suggest various improvements including to the documentation, suggest optimized parameters for the video encoders from your experiences using live streaming or video editing software, or become a community helper at [Discord](https://discord.gg/wDNGDeSW5F).

As the relatively permissive license compared to similar projects is for the benefit of the community, please do not take advantage of it. If improvements are not merged, it will ultimately lead to the project becoming unsustainable. We need your help to continue maintaining performance and quality, staying competent compared to proprietary applications.

Please join our [Discord](https://discord.gg/wDNGDeSW5F) server, then start out with the [Issues](https://github.com/selkies-project/selkies-gstreamer/issues) to see if new enhancements that you can make or things that you want solved have been already raised.

We use Docker containers for building every commit. The root directory [`Dockerfile`](/Dockerfile) and Dockerfiles within the [`addons`](/addons) directory provide directions for building each component, so that you may replicate the procedures in your own setup even without Docker. When contributing, please follow the overall style of the code, and the names of all variables, classes, or functions have to be unambiguous and as less generic as possible.

If you want new features or improvements but if you are not a developer or lack enough time, please consider offering bounties by contacting us. If you want new features that currently are not yet available with [GStreamer](https://gstreamer.freedesktop.org), we must fund the small pool of full-time GStreamer developers capable of implementing new features in order to bring them to Selkies-GStreamer as well. Such issues are tagged as requiring an upstream plugin from GStreamer. Even for features or improvements that are ready to be implemented, crowdfunding bounties motivate developers to solve them faster.

## GStreamer advices

**NOTE: an easier and more accurate way to identify GStreamer object properties is to use `gst-inspect-1.0 element_to_look`.** This will show all properties, including those of parents.

Otherwise, any [GStreamer](https://gstreamer.freedesktop.org) plugin [documentation page](https://gstreamer.freedesktop.org/documentation/plugins_doc.html) is supposed to have a **Hierarchy** section. As all GStreamer objects are defined as **classes** used with object-oriented programming, any properties that you see in parent classes are also properties that you may use for your own classes and plugins. Therefore, all contributors implementing or modifying code relevant to GStreamer are also to carefully check parent classes as well when configuring [properties](https://gstreamer.freedesktop.org/documentation/plugin-development/basics/args.html) or [capabilities](https://gstreamer.freedesktop.org/documentation/gstreamer/gstcaps.html).
