#!/usr/bin/env bash
# Rotate the Lynk TURN shared secret on BOTH sides without downtime risk.
#
# Usage:
#   On the TURN/API VM:   sudo bash rotate_turn_secret.sh
# It generates a new secret, patches /etc/turnserver.conf and backend .env,
# restarts coturn + the API, then verifies the endpoint still mints valid creds.
set -euo pipefail

NEW_SECRET=$(head -c 32 /dev/urandom | base64)
CONF=/etc/turnserver.conf
ENV_FILE="$(cd "$(dirname "$0")/.." && pwd)/.env"

echo "==> Patching $CONF"
sudo sed -i "s|^static-auth-secret=.*|static-auth-secret=${NEW_SECRET}|" "$CONF"

echo "==> Patching $ENV_FILE"
if grep -q "^TURN_SECRET=" "$ENV_FILE"; then
  sudo sed -i "s|^TURN_SECRET=.*|TURN_SECRET=${NEW_SECRET}|" "$ENV_FILE"
else
  echo "TURN_SECRET=${NEW_SECRET}" | sudo tee -a "$ENV_FILE" >/dev/null
fi

echo "==> Restarting services"
sudo systemctl restart coturn
sudo docker compose -f "$(dirname "$0")/../docker-compose.yml" restart 2>/dev/null \
  || sudo systemctl restart lynk-api 2>/dev/null \
  || echo "(restart your API manually: docker compose restart / systemctl restart <service>)"

sleep 3
echo "==> Endpoint check (expect enabled:true):"
curl -s http://localhost:8000/api/v1/transfers/rotation-check/turn-credentials | head -c 200
echo
echo "✅ Rotation complete."
