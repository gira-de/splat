#!/usr/bin/env bash
set -e

PUID=${PUID:-1001}
PGID=${PGID:-1001}

# remap group/user if needed
if [ "$PGID" != "$(getent group splatuser | cut -d: -f3)" ]; then
  groupmod -g "$PGID" splatuser
fi
if [ "$PUID" != "$(id -u splatuser)" ]; then
  usermod -u "$PUID" -g "$PGID" splatuser
fi

# fix mounts
chown -R splatuser:splatuser /splat/test-drive /splat/splat.yaml || true

# drop to splatuser and exec
exec gosu splatuser "$@"