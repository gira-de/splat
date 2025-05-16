#!/usr/bin/env bash
set -euo pipefail

# detect runtime host UID/GID
HOST_UID=$(id -u)
HOST_GID=$(id -g)
SPLAT_UID=$(getent passwd splatuser | cut -d: -f3) # 1000 by default

# only if host and splatuser UID missmatch
if [ "$HOST_UID" != "$SPLAT_UID" ]; then
  PASSWD=/tmp/passwd
  GROUP=/tmp/group

  cp /etc/passwd "$PASSWD"
  cp /etc/group  "$GROUP"
  echo "hostuser:x:${HOST_UID}:${HOST_GID}::/home/hostuser:/bin/sh" >> "$PASSWD"
  echo "hostgroup:x:${HOST_GID}:" >> "$GROUP"

  export NSS_WRAPPER_PASSWD="$PASSWD"
  export NSS_WRAPPER_GROUP="$GROUP"
  export LD_PRELOAD="libnss_wrapper.so"
fi

exec "$@"