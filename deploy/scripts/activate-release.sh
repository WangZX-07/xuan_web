#!/usr/bin/env bash
set -euo pipefail

if [[ $# -ne 1 ]]; then
  echo "usage: activate-release.sh /opt/lungtic/releases/<release-id>" >&2
  exit 2
fi

candidate="$(realpath "$1")"
case "$candidate" in
  /opt/lungtic/releases/*) ;;
  *) echo "release must be inside /opt/lungtic/releases" >&2; exit 2 ;;
esac

test -f "$candidate/public-web/index.html"
test -f "$candidate/admin-web/index.html"
test -f "$candidate/server/app/main.py"
test -d "$candidate/wheelhouse"

if [[ ! -x "$candidate/venv/bin/uvicorn" ]]; then
  python3 -m venv "$candidate/venv"
  "$candidate/venv/bin/python" -m pip install \
    --no-index \
    --find-links="$candidate/wheelhouse" \
    lungtic-control-service
fi

previous="$(readlink -f /opt/lungtic/current || true)"
ln -sfn "$candidate" /opt/lungtic/.current-next
mv -Tf /opt/lungtic/.current-next /opt/lungtic/current

healthy=false
if sudo systemctl restart lungtic-control.service; then
  for _attempt in {1..20}; do
    if curl --fail --silent --show-error http://127.0.0.1:9100/healthz >/dev/null; then
      healthy=true
      break
    fi
    sleep 1
  done
fi

if [[ "$healthy" != true ]]; then
  if [[ -n "$previous" && -d "$previous" ]]; then
    ln -sfn "$previous" /opt/lungtic/.current-rollback
    mv -Tf /opt/lungtic/.current-rollback /opt/lungtic/current
    sudo systemctl restart lungtic-control.service
  fi
  exit 1
fi
