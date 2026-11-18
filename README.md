# FWA Mesh

The deployment behind **[fwamesh.net](https://fwamesh.net)**: a live map, packet analyzer and MQTT observer feed
for the Fort Wayne, Indiana [MeshCore](https://meshcore.co.uk/) LoRa mesh.

FWA Mesh is a local resource. The network itself is community-built: see
[NEIMesh](https://neimesh.net/) (the Northeast Indiana MeshCore co-op), [OKI Mesh](https://okimesh.org/)
(Indiana, Ohio and Kentucky) and [HOOP](https://mutiny19.github.io/hoop/) (the statewide Indiana signpost).

It's a small Docker Compose stack, meant to be easy to fork for another area.

## What's in it

```
observers (repeater + meshcoretomqtt) ──MQTT:1883──▶ ┌────────────── corescope container ──────────────┐
                                                    │ Mosquitto ─▶ ingestor ─▶ SQLite ─▶ web/API/ws   │──:8090──▶ map.<domain>
                                                    └─────────────────────────────────────────────────┘
                                         nginx: static landing page (landing/) ──────────:8091──▶ <domain>
```

| Path | What |
|---|---|
| `docker-compose.yml` | Two services: [CoreScope](https://github.com/Kpa-clawbot/CoreScope) (pinned image, bundled Mosquitto, Caddy disabled) and nginx serving `landing/` |
| `config.example.json` | CoreScope config used by fwamesh.net, with the secrets replaced by placeholders |
| `landing/` | Static landing page and observer guide. No build step. Site-wide URLs live in `landing/config.js` |
| `overrides/build-supervisord-override.sh` | Generates a supervisor config from the pinned CoreScope image that adds `-poll-ms 250`, for lower live-map latency |

## Run it

Requires Docker with the Compose plugin.

```bash
git clone https://github.com/Bgilsing/fwamesh.git && cd fwamesh
mkdir -p corescope-data
cp config.example.json corescope-data/config.json
#   edit corescope-data/config.json: apiKey, CARTO key, trustedProxies, regions, branding, map center
chmod 600 corescope-data/config.json
./overrides/build-supervisord-override.sh   # needs Docker; rerun after every CoreScope image upgrade
docker compose up -d
```

- Analyzer: `http://<host>:8090` · Landing page: `http://<host>:8091` · MQTT: `<host>:1883`
- Health: `curl -s localhost:8090/api/healthz`
- Watch raw MQTT: `docker exec fwamesh-corescope mosquitto_sub -h localhost -t 'meshcore/#' -v`

For production, put a TLS reverse proxy in front of 8090 and 8091 (fwamesh.net uses
[Pangolin](https://github.com/fosrl/pangolin)). WebSockets must pass through to the analyzer, and `/api/*` must
not be cached. Forward TCP 1883 straight to the host for observers. Set `webSocket.trustedProxies` to the proxy's
address so CoreScope's per-client limits work.

## Configuration notes

- **Regions:** `observerIATAWhitelist` accepts only observers publishing under listed airport codes
  (`meshcore/<IATA>/<pubkey>/...`). fwamesh.net accepts FWA plus 16 surrounding Indiana, Ohio and Michigan codes,
  with friendly names in `regions` and one-tap groups in `regionQuickPicks`. To add an area, add its code to
  all three and to the table in `landing/join.html`.
- **Channels:** `channelKeys.Public` decrypts the Public channel. Add hashtag channels (e.g. `"#nei"`) to `hashChannels`.
- **Map:** defaults to CARTO Dark Matter for node contrast. CARTO needs a free key since 2026-08. A bad or missing
  key doesn't error: tiles come back stamped "API KEY REQUIRED", so check a tile by eye. With no key,
  `esri-darkgray-labels` is a good dark default.
- **MQTT is anonymous** (CoreScope's bundled Mosquitto). That's simplest for observers, but anyone can publish.
  Add a Mosquitto password file or ACL if spoofed data becomes a problem.
- **Landing page live stats** fetch `/api/stats` from the analyzer domain, which needs the landing origin listed
  in `corsAllowedOrigins`.
- **Backups:** `curl -H "X-API-Key: <apiKey>" localhost:8090/api/backup -o backup.db`. Don't copy the live database.

## Live-map latency

Measured from MQTT arrival to WebSocket push, on fwamesh.net:

| | median | max |
|---|---|---|
| CoreScope default (`-poll-ms 1000`) | 631 ms | 999 ms |
| With the override (`-poll-ms 250`) | 139 ms | 260 ms |

`liveMap.propagationBufferMs` is 3000 (default 5000). It only matters to viewers who enable "Realistic
propagation", which waits so one transmission's copies from different observers animate together. On this mesh
each extra repeater hop adds about 0.7–1 s.

## Upgrading CoreScope

Bump the image tag in `docker-compose.yml` (see [releases](https://github.com/Kpa-clawbot/CoreScope/releases)),
then:

```bash
./overrides/build-supervisord-override.sh && docker compose up -d
```

## Credits and license

- [CoreScope](https://github.com/Kpa-clawbot/CoreScope) (GPL-3.0) does the real work. This repo only configures it
  and runs the published image.
- Radio, repeater and channel recommendations on the landing page come from [NEIMesh](https://neimesh.net/).
- The files in this repository are MIT-licensed. See [LICENSE](LICENSE).
