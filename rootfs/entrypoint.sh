#!/bin/bash

set -eu

# ----------------------------------------
# Validate environment variables
# ----------------------------------------
: "${TEST_TIMEOUT:=300}"

if [[ ! "${TEST_TIMEOUT}" =~ ^[1-9][0-9]*$ ]]; then
    echo "ERROR: TEST_TIMEOUT must be a positive integer." >&2
    exit 1
fi

if (( TEST_TIMEOUT > 3600 )); then
    echo "ERROR: TEST_TIMEOUT must not exceed 3600 seconds." >&2
    exit 1
fi

export CHECKTIMEOUT="${TEST_TIMEOUT}"
export SECRET_KEY="${SECRET_KEY:-$(openssl rand -hex 32)}"
UWSGI_READ_TIMEOUT=$(( TEST_TIMEOUT + 10 ))

# ----------------------------------------
# Generate Nginx configuration
# ----------------------------------------
NGINX_TEMPLATE="/etc/nginx/templates/default.conf.template"
NGINX_CONFIG="/etc/nginx/sites-enabled/default"
TIMEOUT_PLACEHOLDER="@@UWSGI_READ_TIMEOUT@@"

if [[ ! -f "${NGINX_TEMPLATE}" ]]; then
    echo "ERROR: Nginx template not found: ${NGINX_TEMPLATE}" >&2
    exit 1
fi

if ! grep -Fq "${TIMEOUT_PLACEHOLDER}" "${NGINX_TEMPLATE}"; then
    echo "ERROR: Timeout placeholder not found in ${NGINX_TEMPLATE}" >&2
    exit 1
fi

sed "s/${TIMEOUT_PLACEHOLDER}/${UWSGI_READ_TIMEOUT}/g" \
    "${NGINX_TEMPLATE}" > "${NGINX_CONFIG}"

# ----------------------------------------
# Validate Nginx configuration
# ----------------------------------------
if ! nginx -t; then
    echo "ERROR: Nginx configuration validation failed." >&2
    exit 1
fi

# ----------------------------------------
# Start the requested process
# ----------------------------------------
exec "$@"
