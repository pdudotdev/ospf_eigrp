# HashiCorp Vault Setup

aiNOC uses Vault to store 4 secrets (router credentials, Jira API token, Discord bot token).
Vault is optional — the system falls back to `.env` values when not configured.

---

## Install Vault

```bash
wget -O - https://apt.releases.hashicorp.com/gpg | sudo gpg --dearmor -o /usr/share/keyrings/hashicorp-archive-keyring.gpg
echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/hashicorp-archive-keyring.gpg] https://apt.releases.hashicorp.com $(grep -oP '(?<=UBUNTU_CODENAME=).*' /etc/os-release || lsb_release -cs) main" | sudo tee /etc/apt/sources.list.d/hashicorp.list
sudo apt update && sudo apt install vault
```

## Start Vault (dev mode — lab only)

```bash
vault server -dev -dev-root-token-id="dev-root-token" &
export VAULT_ADDR='http://127.0.0.1:8200'
export VAULT_TOKEN='dev-root-token'
```

> For production: use persistent storage backend + AppRole auth + audit logging.

## Store Secrets

```bash
vault kv put secret/ainoc/router username=<router_username> password=<router_password>
vault kv put secret/ainoc/jira api_token=<jira_api_token>
vault kv put secret/ainoc/discord bot_token=<discord_bot_token>
```

## Verify

```bash
vault kv get secret/ainoc/router
vault kv get secret/ainoc/jira
vault kv get secret/ainoc/discord
```

## Configure aiNOC

Add to `.env`:
```
VAULT_ADDR=http://127.0.0.1:8200
VAULT_TOKEN=dev-root-token
```

When these are set, `core/vault.py` reads secrets from Vault instead of `.env`.
If Vault is unreachable, it falls back to `ROUTER_USERNAME`/`ROUTER_PASSWORD`/etc. in `.env`.

## Vault Paths Reference

| Path | Keys | Used by |
|------|------|---------|
| `secret/ainoc/router` | `username`, `password` | `core/settings.py` |
| `secret/ainoc/jira` | `api_token` | `core/jira_client.py` |
| `secret/ainoc/discord` | `bot_token` | `core/discord_approval.py` |
