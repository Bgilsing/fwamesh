#!/bin/sh
# Generates overrides/corescope-index.html: CoreScope's own /app/public/index.html from the image pinned in
# docker-compose.yml, with the Umami tracker added before </head> so analyzer visits are counted too.
# CoreScope routes with #hashes (no pushState), which Umami doesn't see, so a small listener reports each
# hash change as a page view.
#
# Reads UMAMI_MAP_WEBSITE_ID, UMAMI_TRACKER_URL and (optional) UMAMI_MAP_DOMAIN from .env. If the ID is empty, the page is copied unchanged.
# Run it after cloning and again after every CoreScope image upgrade, then `docker compose up -d corescope`.
#
#   ./overrides/build-corescope-index.sh
set -eu
cd "$(dirname "$0")/.."
IMAGE=$(sed -n 's/^ *image: *\(ghcr.io\/kpa-clawbot\/corescope:[^ ]*\).*/\1/p' docker-compose.yml | head -1)
[ -n "$IMAGE" ] || { echo "could not find the corescope image in docker-compose.yml" >&2; exit 1; }
SRC=/app/public/index.html
OUT=overrides/corescope-index.html

getenv() { [ -f .env ] && sed -n "s/^$1=//p" .env | tail -1 || true; }
WEBSITE_ID=$(getenv UMAMI_MAP_WEBSITE_ID)
TRACKER_URL=$(getenv UMAMI_TRACKER_URL)
MAP_DOMAIN=$(getenv UMAMI_MAP_DOMAIN)   # only count visits on this hostname (skips LAN/IP access)

docker pull -q "$IMAGE" >/dev/null
docker run --rm --entrypoint cat "$IMAGE" "$SRC" > "$OUT.orig"
[ "$(grep -c '</head>' "$OUT.orig")" = 1 ] || { rm -f "$OUT.orig"; echo "unexpected $SRC layout in $IMAGE; not patching" >&2; exit 1; }

if [ -z "$WEBSITE_ID" ]; then
  mv "$OUT.orig" "$OUT"
  echo "wrote $OUT unchanged (UMAMI_MAP_WEBSITE_ID not set)"
  exit 0
fi
[ -n "$TRACKER_URL" ] || { rm -f "$OUT.orig"; echo "set UMAMI_TRACKER_URL in .env" >&2; exit 1; }
TRACKER_URL=${TRACKER_URL%/}
DOMAINS_ATTR=""
[ -n "$MAP_DOMAIN" ] && DOMAINS_ATTR=" data-domains=\"$MAP_DOMAIN\""

SNIPPET="  <!-- Added by overrides/build-corescope-index.sh: Umami analytics -->
  <script defer src=\"$TRACKER_URL/script.js\" data-website-id=\"$WEBSITE_ID\" data-host-url=\"$TRACKER_URL\"$DOMAINS_ATTR></script>
  <script>(function(){var prev=location.href;addEventListener('hashchange',function(){var url=location.href,ref=prev.replace(location.origin,'');prev=url;if(window.umami)umami.track(function(p){return Object.assign({},p,{url:url,referrer:ref,title:document.title});});});})();</script>"

awk -v snippet="$SNIPPET" '/<\/head>/ && !done { print snippet; done=1 } { print }' "$OUT.orig" > "$OUT.tmp"
rm -f "$OUT.orig"
grep -q "$WEBSITE_ID" "$OUT.tmp" || { rm -f "$OUT.tmp"; echo "patch did not apply" >&2; exit 1; }
mv "$OUT.tmp" "$OUT"
echo "wrote $OUT ($IMAGE, Umami website $WEBSITE_ID via $TRACKER_URL)"
