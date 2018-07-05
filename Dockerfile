# Dockerfile for running keep-on-giffing test suite
ARG PYTHON_TAG=3.7-stretch

FROM python:${PYTHON_TAG}
LABEL maintainer="Marti Raudsepp <marti@juffo.org>"

# WTF Docker is retarded, this CAN NOT appear at the beginning of the file
# https://github.com/moby/moby/issues/34129
ARG APT_PKG=ffmpeg
RUN apt-get update && \
    apt-get install -y $APT_PKG --no-install-recommends

# Make requirements cache-able
COPY requirements*txt /keep-on-giffing/
WORKDIR /keep-on-giffing
RUN pip install -r requirements-dev.txt

COPY . /keep-on-giffing/
RUN pip install -e '.[dev]'
RUN pytest
