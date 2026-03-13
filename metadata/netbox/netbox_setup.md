# NetBox Setup

aiNOC uses NetBox as the source of truth for device inventory (replacing `NETWORK.json`).
NetBox is optional — the system falls back to `inventory/NETWORK.json` when not configured.

---

## Install NetBox (Docker)

```bash
git clone -b release https://github.com/netbox-community/netbox-docker.git
cd netbox-docker
```

## Configure Port Mapping

Rename the existing test override file (it's empty) and edit it to expose port 8080:

```bash
sudo mv docker-compose.test.override.yml docker-compose.override.yml
```

Edit `docker-compose.override.yml` to contain:
```yaml
services:
  netbox:
    ports:
      - "127.0.0.1:8000:8080"
```

## Start Containers

```bash
docker compose up -d
```

First start takes ~2 minutes to run database migrations. All containers will show `healthy` when ready.

## Create Superuser

```bash
docker compose exec -e DJANGO_SUPERUSER_PASSWORD=<password> netbox \
  python /opt/netbox/netbox/manage.py createsuperuser \
  --username admin --email admin@ainoc.local --noinput
```

Then restart to apply the port mapping:
```bash
docker compose down && docker compose up -d
```

## Create API Token

1. Log in at `http://localhost:8000` with admin / <your_password>
2. Go to the user menu (top right) → **Profile** → **API Tokens** → **Add Token**
3. Under **Version**, select **v1** — v2 tokens are hashed and incompatible with pynetbox
4. Copy the generated token value (shown once at creation)

## Configure aiNOC

Add to `.env`:
```
NETBOX_URL=http://localhost:8000
NETBOX_TOKEN=<your_api_token>
```

## Populate Devices

Run the population script — it creates all prerequisite objects and 9 devices automatically:

```bash
cd /home/mcp/aiNOC
python metadata/netbox/populate_netbox.py
```

The script is idempotent — safe to run multiple times. Verify the result:

```bash
PYTHONPATH=/home/mcp/aiNOC python -c "
from core.netbox import load_devices
d = load_devices()
print(f'{len(d)} devices loaded from NetBox')
for name, info in sorted(d.items()):
    print(f'  {name}: {info[\"host\"]} ({info[\"transport\"]})')
"
```

## Device Reference

| Device | Platform slug | Transport | cli_style | Management IP | Site |
|--------|--------------|-----------|-----------|---------------|------|
| A1C | cisco_iosxe | asyncssh | ios | 172.20.20.205 | Access |
| A2C | cisco_iosxe | asyncssh | ios | 172.20.20.206 | Access |
| C1C | cisco_iosxe | restconf | ios | 172.20.20.207 | Core |
| C2C | cisco_iosxe | restconf | ios | 172.20.20.208 | Core |
| E1C | cisco_iosxe | restconf | ios | 172.20.20.209 | Edge |
| E2C | cisco_iosxe | restconf | ios | 172.20.20.210 | Edge |
| IAN | cisco_iosxe | asyncssh | ios | 172.20.20.220 | ISP A |
| IBN | cisco_iosxe | asyncssh | ios | 172.20.20.230 | ISP B |
| X1C | cisco_iosxe | restconf | ios | 172.20.20.240 | Remote |
