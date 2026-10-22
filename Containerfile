# Builder image for the "Hacked" font. Holds every build dependency and the
# pinned upstream sources, so builds run offline and leave nothing on the host
# but this image and the output fonts.
FROM docker.io/library/debian:trixie-slim

ARG HACK_REF=v3.003
ARG ALT_HACK_COMMIT=9fab7328cfc208046cb7f3d713ec97a724d8219a

# ttfautohint 1.8.4 from trixie is newer than the 1.7 Hack's own script compiles.
RUN apt-get update \
 && apt-get install -y --no-install-recommends \
        ca-certificates git python3 python3-venv ttfautohint \
 && rm -rf /var/lib/apt/lists/*

COPY container/requirements.lock /tmp/requirements.lock
RUN python3 -m venv /opt/venv \
 && /opt/venv/bin/pip install --no-cache-dir -r /tmp/requirements.lock \
 && rm /tmp/requirements.lock
ENV PATH=/opt/venv/bin:$PATH

RUN git clone --quiet --depth 1 --branch "$HACK_REF" https://github.com/source-foundry/Hack.git /opt/src/hack \
 && git init --quiet /opt/src/alt-hack \
 && git -C /opt/src/alt-hack fetch --quiet --depth 1 https://github.com/source-foundry/alt-hack.git "$ALT_HACK_COMMIT" \
 && git -C /opt/src/alt-hack checkout --quiet FETCH_HEAD

# Build scripts and config are bind-mounted at run time (see build.sh), so
# changing the glyph picks doesn't need an image rebuild.
ENTRYPOINT ["/bin/bash", "/work/container/build-font.sh"]
