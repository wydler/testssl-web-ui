# ----------------------------------------
# Stage 1: Build / Download testssl.sh
# ----------------------------------------
FROM alpine:3.24.3@sha256:be2656061b536c1883c4034790e21d0a09c5aaaf51968b89368a3c0371ea2c9a AS builder

# Build-Argument
ARG APP_VERSION

# Setze Arbeitsverzeichnis für temporäre Dateien
WORKDIR /tmp

# ----------------------------------------
# Installiere wget und ca-certificates für HTTPS-Download
# --no-install-recommends hält das Image klein
# ----------------------------------------
RUN apk add --no-cache \
    ca-certificates \
    git

# ----------------------------------------
# Create /opt/testssl.sh directory and download the latest testssl.sh release
# ----------------------------------------
RUN set -eux; \
    test -n "${APP_VERSION}"; \
    git init /opt/testssl.sh; \
    cd /opt/testssl.sh; \
    git remote add origin https://github.com/testssl/testssl.sh.git; \
    git fetch --depth 5 origin \
        "refs/tags/${APP_VERSION}:refs/tags/${APP_VERSION}"; \
    git checkout "refs/tags/${APP_VERSION}"; \
    git log -n 5 > git-log.txt; \
    rm -rf .git bin/openssl.Darwin.x86_64 bin/openssl.FreeBSD.amd64


# ----------------------------------------
# Stage 2: Runtime
# ----------------------------------------
FROM alpine:3.24.3@sha256:be2656061b536c1883c4034790e21d0a09c5aaaf51968b89368a3c0371ea2c9a

# Build-Argument
ARG APP_VERSION
ARG DOCKER_IMAGE_VERSION

# ----------------------------------------
# Setze Umgebungsvariablen
# UWSGI_PROCESSES   Number of uWSGI processes: amount of max. parallel running SSL checks
# UWSGI_THREADS     Number of uWSGI threads: amount of max. parallel running SSL checks
# TEST_TIMEOUT      Set the timeout for the portal site (default 300 seconds)
# TESTSSLDEBUG      Enable debugging for testssl.sh by setting this variable to a higher value
# ----------------------------------------
ENV UWSGI_PROCESSES=4 \
    UWSGI_THREADS=2 \
    TEST_TIMEOUT=300 \
    TESTSSLDEBUG=0

# ----------------------------------------
# OCI image metadata
# ----------------------------------------    
LABEL org.opencontainers.image.authors="Daniel Wydler" \
      org.opencontainers.image.description="Web frontend for testssl.sh." \
      org.opencontainers.image.documentation="https://github.com/wydler/testsslsh-gui/blob/master/README.md" \
      org.opencontainers.image.source="https://github.com/wydler/testsslsh-gui" \
      org.opencontainers.image.title="wydler//testsslsh-gui" \
      org.opencontainers.image.url="https://hub.docker.com/r/wydler/testsslsh-gui" \
      org.opencontainers.image.version="${DOCKER_IMAGE_VERSION}" \
      org.opencontainers.image.base.name="alpine:3.22" \
      org.opencontainers.image.testssl.version="${APP_VERSION}"

# ----------------------------------------
# Runtime dependencies
# ----------------------------------------      
RUN apk add --no-cache \
    aha \
    bash \
    bind-tools \
    coreutils \
    net-tools \
    nginx \
    openssl \
    procps-ng \
    py3-flask \
    py3-setuptools \
    python3 \
    socat \
    supervisor \
    uwsgi \
    uwsgi-python3 \
    util-linux-misc \
    xxd \
 && adduser -S -D -H -G www-data www-data \
 && mkdir -p /etc/nginx/sites-enabled

# ----------------------------------------
# Application files and configuration
# ----------------------------------------
COPY --from=builder /opt/testssl.sh /opt/testssl.sh

COPY rootfs /

RUN chmod 0755 /entrypoint.sh \
 && cp /etc/supervisor/conf.d/supervisord.conf /etc/supervisord.conf \
 && sed -i 's#/usr/bin/uwsgi#/usr/sbin/uwsgi#' /etc/supervisord.conf

WORKDIR /var/www/html/testssl

EXPOSE 5000

ENTRYPOINT ["/entrypoint.sh"]
CMD ["/usr/bin/supervisord", "-c", "/etc/supervisord.conf"]
