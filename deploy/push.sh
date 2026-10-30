#!/usr/bin/env bash
# From the laptop: bundle the committed code, the showroom and the server .env, upload
# them to the VM and run vm-deploy.sh there.
#   bash deploy/push.sh
# The server .env is built from scratch (never copied from anywhere else): the Meta key
# from this repo's .env, plus the PMS_* settings below. The live access code is kept in
# out/live-code.txt (git-ignored) so it can go in the submission.
set -euo pipefail
cd "$(dirname "$0")/.."
PROJECT=project-05cd29cd-d211-4cec-957; ZONE=us-west1-b; VM=psp
B=$(mktemp -d)/bundle; mkdir -p "$B"
git diff --quiet HEAD -- . ':!out' || { echo "commit first: the server runs the committed code"; exit 1; }
git archive --format=tar HEAD > "$B/app.tar"
git ls-files --others --ignored --exclude-standard inspo | COPYFILE_DISABLE=1 tar -cf "$B/inspo-shots.tar" -T -
uv run scripts/showroom.py stage "$B/out"
[ -s out/live-code.txt ] || python3 -c "import secrets; print('pms-' + secrets.token_hex(4))" > out/live-code.txt
{
  grep '^MODEL_API_KEY=' .env
  echo "PMS_LIVE=code"
  echo "PMS_LIVE_CODE=$(cat out/live-code.txt)"
  echo "PMS_MAX_RUNNING=1"
  echo "PMS_LIVE_PER_DAY=12"
  echo "PMS_BASE_URL=https://pimpmysocial.loreto.io"
} > "$B/env"
chmod 600 "$B/env"
cp deploy/vm-deploy.sh "$B/"
COPYFILE_DISABLE=1 tar -czf "$B.tgz" -C "$(dirname "$B")" bundle
rm -rf "$B"
echo "uploading $(du -h "$B.tgz" | cut -f1)"
gcloud compute scp "$B.tgz" "jeremy@$VM:/tmp/pms-bundle.tgz" --zone $ZONE --project $PROJECT --tunnel-through-iap
rm -f "$B.tgz"
gcloud compute ssh "jeremy@$VM" --zone $ZONE --project $PROJECT --tunnel-through-iap --command \
  'set -e; rm -rf /tmp/pms-bundle && mkdir /tmp/pms-bundle && tar -xzf /tmp/pms-bundle.tgz -C /tmp/pms-bundle --strip-components=1 && bash /tmp/pms-bundle/vm-deploy.sh /tmp/pms-bundle; rm -rf /tmp/pms-bundle /tmp/pms-bundle.tgz'
