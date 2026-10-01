# 32-bit Raspberry Pi OS equivalent (armhf userland on an armv7 CPU). Build on a non-ARM host via
# QEMU binfmt: docker build --platform linux/arm/v7 -f docker/armv7/lauschkiste.Dockerfile .
FROM --platform=linux/arm/v7 debian:trixie-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    libasound2-dev \
    libportaudio2 \
    pulseaudio \
    pulseaudio-utils \
    && rm -rf /var/lib/apt/lists/*

ARG UID=1000
ARG USER=pi
ARG HOME=/home/${USER}
ENV INSTALLATION_PATH=${HOME}/lauschkiste

RUN useradd -m -u "${UID}" "${USER}" && usermod -aG pulse "${USER}"

# No wheels on PyPI for armv7l: cffi (via sounddevice) and evdev are built from source.
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential ca-certificates curl \
    libffi-dev \
    python3 python3-venv python3-dev \
    && rm -rf /var/lib/apt/lists/*

ADD https://astral.sh/uv/install.sh /uv-installer.sh
RUN UV_INSTALL_DIR=/usr/local/bin sh /uv-installer.sh && rm /uv-installer.sh

COPY --chown=${USER}:${USER} . ${INSTALLATION_PATH}/

USER ${USER}
WORKDIR ${INSTALLATION_PATH}

ENV VIRTUAL_ENV=${INSTALLATION_PATH}/.venv
RUN python3 -m venv --system-site-packages $VIRTUAL_ENV
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

RUN uv sync --no-dev --frozen

EXPOSE 5556

CMD ["lauschkiste"]
