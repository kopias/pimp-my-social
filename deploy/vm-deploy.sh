#!/usr/bin/env bash
# Runs ON the VM (as a sudoer), from the unpacked bundle that deploy/push.sh uploads:
#   bundle/app.tar      the repo at the commit being deployed (git archive)
#   bundle/out/         the showroom: out/jobs/<id> + out/showroom.json
#   bundle/inspo-shots.tar  template screenshots (kept out of git; live builds look at them)
#   bundle/env          the app's .env (only the Meta key and PMS_* settings, nothing of loreto's)
# Idempotent. Never touches another app's files, unit or vhost.
set -euo pipefail
export PATH="$PATH:/usr/sbin:/sbin"
B=${1:?bundle dir}
S=/srv/pimp-my-social
log(){ echo "[pms $(date -u +%T)] $*"; }

id pms >/dev/null 2>&1 || { log "creating user pms"; sudo useradd --system --home-dir $S/home --shell /usr/sbin/nologin pms; }
sudo mkdir -p $S/app $S/home $S/browsers
log "code"
sudo find $S/app -mindepth 1 -maxdepth 1 ! -name out ! -name .env -exec rm -rf {} +
sudo tar -xf "$B/app.tar" -C $S/app
sudo tar -xf "$B/inspo-shots.tar" -C $S/app
log "showroom"
sudo mkdir -p $S/app/out
# no --delete: makeovers judges run live on the server live in the same folder
sudo rsync -a "$B/out/jobs/" $S/app/out/jobs/
sudo cp "$B/out/showroom.json" $S/app/out/showroom.json
sudo install -m 600 "$B/env" $S/app/.env
sudo chown -R pms:pms $S
sudo chmod 750 $S

if [ ! -x $S/venv/bin/uvicorn ] || [ "$B/app.tar" -nt $S/venv/.stamp ]; then
  log "python deps"
  sudo -u pms python3 -m venv $S/venv
  sudo -u pms $S/venv/bin/pip install -q --upgrade pip uv
  sudo -u pms $S/venv/bin/uv pip install -q --python $S/venv/bin/python -r $S/app/pyproject.toml
  sudo -u pms touch $S/venv/.stamp
fi
if [ -z "$(sudo ls $S/browsers 2>/dev/null)" ]; then
  log "chromium for live makeovers"
  sudo $S/venv/bin/playwright install-deps chromium >/dev/null
  sudo -u pms env PLAYWRIGHT_BROWSERS_PATH=$S/browsers $S/venv/bin/playwright install chromium >/dev/null
fi

log "service"
sudo install -m 644 $S/app/deploy/pimpmysocial.service /etc/systemd/system/pimpmysocial.service
sudo systemctl daemon-reload
sudo systemctl enable -q pimpmysocial
sudo systemctl restart pimpmysocial
for i in $(seq 1 20); do curl -fsS -o /dev/null http://127.0.0.1:8180/api/config && break; sleep 1; done
curl -fsS http://127.0.0.1:8180/api/config >/dev/null && log "app answers on :8180" || { log "FATAL: app not answering"; sudo journalctl -u pimpmysocial -n 30 --no-pager; exit 1; }

log "vhost"
sudo install -m 644 $S/app/deploy/pimpmysocial.conf /etc/nginx/sites-available/pimpmysocial.conf
if sudo test -f /etc/letsencrypt/live/pimpmysocial.loreto.io/fullchain.pem; then
  sudo ln -sf /etc/nginx/sites-available/pimpmysocial.conf /etc/nginx/sites-enabled/pimpmysocial.conf
  sudo nginx -t 2>&1 | tail -1
  sudo systemctl reload nginx
  log "nginx reloaded"
else
  log "no certificate yet: run play-smooth-piano/deploy/shared/cert-and-enable.sh with APP=pimpmysocial DOMAINS=pimpmysocial.loreto.io"
fi
