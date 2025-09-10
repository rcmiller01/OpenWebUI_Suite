#!/usr/bin/env bash
set -euo pipefail

SUITE_DIR="/opt/openwebui-suite"
GW_DIR="$SUITE_DIR/00-pipelines-gateway"
ENV_FILE="$SUITE_DIR/.env.prod"
DB_PATH="$GW_DIR/data/gateway.db"
UNIT="owui-00-pipelines-gateway.service"
UVICORN_BIN="$SUITE_DIR/.venv/bin/uvicorn"

say() { printf "\n🔧 %s\n" "$*"; }
die() { printf "\n❌ %s\n" "$*" >&2; exit 1; }

[ -d "$GW_DIR" ] || die "Gateway dir missing: $GW_DIR"
[ -f "$ENV_FILE" ] || die "Env file missing: $ENV_FILE"
[ -x "$UVICORN_BIN" ] || die "Uvicorn not found: $UVICORN_BIN (activate venv & pip install)"

say "Creating DB directory + file…"
sudo mkdir -p "$(dirname "$DB_PATH")"
sudo touch "$DB_PATH"
sudo chown -R root:root "$GW_DIR/data"
sudo chmod 755  "$GW_DIR/data"
sudo chmod 664  "$DB_PATH"

say "Ensuring systemd unit exists and points to the right DB path…"
if [ ! -f "/etc/systemd/system/$UNIT" ]; then
  sudo tee "/etc/systemd/system/$UNIT" >/dev/null <<UNITFILE
[Unit]
Description=OWUI Pipelines Gateway (non-docker)
After=network-online.target
Wants=network-online.target

[Service]
User=root
WorkingDirectory=$GW_DIR
EnvironmentFile=$ENV_FILE
Environment=GATEWAY_DB=$DB_PATH
ExecStart=$UVICORN_BIN src.server:app --host 0.0.0.0 --port 8088
Restart=always
RestartSec=2
LimitNOFILE=65535

[Install]
WantedBy=multi-user.target
UNITFILE
else
  # Ensure Environment= line exists and matches path
  if ! grep -q '^Environment=GATEWAY_DB=' "/etc/systemd/system/$UNIT"; then
    sudo sed -i "/^EnvironmentFile=/a Environment=GATEWAY_DB=$DB_PATH" "/etc/systemd/system/$UNIT"
  else
    sudo sed -i "s#^Environment=GATEWAY_DB=.*#Environment=GATEWAY_DB=$DB_PATH#" "/etc/systemd/system/$UNIT"
  fi
fi

say "Reloading systemd + restarting gateway…"
sudo systemctl daemon-reload
sudo systemctl enable --now "$UNIT"
sleep 1
sudo systemctl restart "$UNIT"
sleep 1

say "Recent logs:"
journalctl -u "$UNIT" -n 80 --no-pager || true

say "Health check:"
if curl -fsS http://127.0.0.1:8088/healthz >/dev/null; then
  echo "✅ gateway OK on :8088"
else
  echo "❌ gateway not responding on :8088"
  ss -lntp | grep 8088 || true
  exit 1
fi
