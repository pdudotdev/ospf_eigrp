"""Runtime configuration — credentials, TLS flags, and transport timeout constants.

Loaded once at import time. All transport modules import from here.
"""
import os
from dotenv import load_dotenv

load_dotenv()

from core.vault import get_secret

USERNAME = get_secret("ainoc/router", "username", fallback_env="ROUTER_USERNAME")
PASSWORD = get_secret("ainoc/router", "password", fallback_env="ROUTER_PASSWORD")

if not USERNAME or not PASSWORD:
    raise RuntimeError("ROUTER_USERNAME and ROUTER_PASSWORD must be set in .env")

# SSH security settings — defaults are lab-safe; set to 'true' in .env for production.
SSH_STRICT_KEY = os.getenv("SSH_STRICT_HOST_KEY", "false").lower() == "true"

# RESTCONF settings — defaults are lab-safe; set RESTCONF_VERIFY_TLS=true for production.
RESTCONF_PORT       = int(os.getenv("RESTCONF_PORT", "443"))
RESTCONF_VERIFY_TLS = os.getenv("RESTCONF_VERIFY_TLS", "false").lower() == "true"

# Scrapli SSH timeout (seconds) applied to all SSH connections.
SSH_TIMEOUT_TRANSPORT = 15   # SSH handshake; devices respond in <5s or are unreachable
SSH_TIMEOUT_OPS       = 30   # Command execution — kept high for slow commands
SSH_TIMEOUT_OPS_LONG  = 45   # For long-running commands (traceroute); IOS finishes in ~30s

# SSH retry settings — applied to transient connection failures only.
SSH_RETRIES     = 1   # One retry after initial failure (2 total); reduces worst-case per-call from 94s → 32s
SSH_RETRY_DELAY = 2   # Seconds between retries
