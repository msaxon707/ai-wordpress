# =========================
# path: config.py  (REPLACE FILE)
# =========================
import os
from dataclasses import dataclass
from urllib.parse import urlparse

def _bool(env: str, default: bool = False) -> bool:
    v = os.getenv(env)
    if v is None:
        return default
    return v.strip().lower() in {"1", "true", "yes", "y", "on"}

def _norm_base_url(raw: str | None) -> str:
    if not raw:
        raise SystemExit("Set WP_BASE_URL (e.g., https://your-site.com)")
    url = raw.strip()
    if not url.startswith(("http://", "https://")):
        url = "https://" + url
    while url.endswith("/"):
        url = url[:-1]
    p = urlparse(url)
    if not p.scheme or not p.netloc:
        raise SystemExit(f"WP_BASE_URL looks invalid: {raw!r}")
    return url

@dataclass(frozen=True)
class Settings:
    # WordPress
    WP_BASE_URL: str = _norm_base_url(os.getenv("WP_BASE_URL", ""))
    WP_USERNAME: str = os.getenv("WP_USERNAME", "")
    WP_APP_PASSWORD: str = os.getenv("WP_APP_PASSWORD", "")

    # OpenAI / model
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    OPENAI_MODEL: str = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    OPENAI_TEMPERATURE: float = float(os.getenv("OPENAI_TEMPERATURE", "0.7"))
    OPENAI_MAX_TOKENS: int = int(os.getenv("OPENAI_MAX_TOKENS", "1200"))

    # Links
    AFFILIATE_DOMAINS: tuple[str, ...] = tuple(
        d.strip()
        for d in os.getenv(
            "AFFILIATE_DOMAINS",
            "amzn.to,amazon.com,shareasale.com,rstyle.me,impact.com",
        ).split(",")
        if d.strip()
    )

    # Misc
    DRY_RUN: bool = _bool("DRY_RUN", False)

SETTINGS = Settings()

if not SETTINGS.WP_USERNAME or not SETTINGS.WP_APP_PASSWORD:
    raise SystemExit("Set WP_USERNAME and WP_APP_PASSWORD (WordPress application password).")
