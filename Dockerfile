FROM python:3-jessie

LABEL maintainer "https://github.com/danisla"

# Install build deps
RUN python3 -m pip install --upgrade build

# Build a python package for the webrtc app.
WORKDIR /opt/pypi

# Copy source files
COPY src ./src
COPY pyproject.toml setup.cfg ./

ARG PYPI_PACKAGE=selkies-gstreamer
ARG PACKAGE_VERSION=1.0.0

# Patch the package name and version
RUN sed -i \
    -e "s|^name =.*|name = ${PYPI_PACKAGE}|g" \
    -e "s|^version =.*|version = ${PACKAGE_VERSION}|g" \
    setup.cfg

RUN python3 -m build
