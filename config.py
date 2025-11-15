import os
from dataclasses import dataclass
from urllib.parse import urlparse

def _bool(env: str, default: bool = False) -> bool:
    v = os.getenv(env)
    if v is None: return default
    return v.strip().lower() in {"1","true","yes","y","on"}

def _norm_base_url(raw: str | None) -> str:
    if not raw: raise SystemExit("Set WP_BASE_URL (e.g., https://your-site.com)")
    url = raw.strip()
    if not url.startswith(("http://","https://")): url = "https://" + url
    while url.endswith("/"): url = url[:-1]
    p = urlparse(url)
    if not p.scheme or not p.netloc: raise SystemExit(f"WP_BASE_URL looks invalid: {raw!r}")
    return url

@dataclass(frozen=True)
class Settings:
    WP_BASE_URL: str = _norm_base_url(os.getenv("WP_BASE_URL", ""))
    WP_USERNAME: str = os.getenv("WP_USERNAME", "")
    WP_APP_PASSWORD: str = os.getenv("WP_APP_PASSWORD", "")
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    OPENAI_MODEL: str = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    OPENAI_TEMPERATURE: float = float(os.getenv("OPENAI_TEMPERATURE", "0.7"))
    OPENAI_MAX_TOKENS: int = int(os.getenv("OPENAI_MAX_TOKENS", "1200"))
    AFFILIATE_DOMAINS: tuple[str, ...] = tuple(
        d.strip() for d in os.getenv(
            "AFFILIATE_DOMAINS",
            "amzn.to,amazon.com,shareasale.com,rstyle.me,impact.com"
        ).split(",") if d.strip()
    )
    DRY_RUN: bool = _bool("DRY_RUN", False)

SETTINGS = Settings()
if not SETTINGS.WP_USERNAME or not SETTINGS.WP_APP_PASSWORD:
    raise SystemExit("Set WP_USERNAME and WP_APP_PASSWORD (WordPress application password).")

# =========================
# path: content_normalizer.py
# =========================
from __future__ import annotations
import html, re
from typing import Iterable
from urllib.parse import urlparse
from bs4 import BeautifulSoup
from markdown import markdown

_HTML_HINT_RE = re.compile(r"</?(p|h[1-6]|a|ul|ol|li|strong|em|blockquote|img|figure)\b", re.I)
_SMART_QUOTES = {"\u201C": '"', "\u201D": '"', "\u201E": '"', "\u201F": '"',
                 "\u2018": "'", "\u2019": "'", "\u2032": "'", "\u2033": '"'}
_MD_LINK_RE = re.compile(r"\[([^\]]+)\]\(([^)\s]+)(?:\s+\"([^\"]+)\")?\)", re.MULTILINE)
_URL_RE = re.compile(r'(?P<pre>^|[\s>])(?P<url>(?:https?://|www\.)[^\s<]+)', re.IGNORECASE)

def _unsmart(s: str) -> str:
    return "".join(_SMART_QUOTES.get(ch, ch) for ch in s)

def _ensure_scheme(url: str) -> str:
    if not url: return url
    p = urlparse(url)
    if not p.scheme:
        if url.startswith("//"): return f"https:{url}"
        if url.startswith(("mailto:","tel:","#")): return url
        return f"https://{url}"
    return url

def markdown_to_html(md_text: str) -> str:
    text = (md_text or "").replace("\r\n","\n").replace("\r","\n").strip()
    return markdown(text, extensions=["extra","sane_lists","attr_list"])

def _convert_md_links_in_htmlish(text: str) -> str:
    def _repl(m: re.Match) -> str:
        label, href, title = m.group(1), m.group(2), m.group(3)
        href = _ensure_scheme(_unsmart(href.strip()))
        title_attr = f' title="{html.escape(title)}"' if title else ""
        return f'<a href="{html.escape(href, quote=True)}"{title_attr}>{html.escape(label)}</a>'
    return _MD_LINK_RE.sub(_repl, text)

def _linkify_bare_urls(html_text: str) -> str:
    def _repl(m: re.Match) -> str:
        pre, url = m.group("pre"), m.group("url")
        href = _ensure_scheme(url)
        return f'{pre}<a href="{html.escape(href, quote=True)}" target="_blank" rel="nofollow noopener sponsored">{html.escape(url)}</a>'
    return _URL_RE.sub(_repl, html_text)

def looks_like_html(text: str) -> bool:
    return bool(_HTML_HINT_RE.search(text or ""))

def fix_affiliate_links(html_text: str, affiliate_domains: Iterable[str] | None = None) -> str:
    if not html_text: return html_text
    html_text = _convert_md_links_in_htmlish(html_text)
    soup = BeautifulSoup(html_text, "html.parser")
    for a in soup.find_all("a"):
        href = _ensure_scheme(_unsmart((a.get("href") or "").strip()))
        if href: a["href"] = href
        a["target"] = "_blank"
        existing_rel = set((a.get("rel") or []))
        new_rels = {"nofollow","noopener"}
        is_affiliate = False
        if affiliate_domains:
            try:
                host = urlparse(href).netloc.lower()
                is_affiliate = any(host.endswith(d.lower()) for d in affiliate_domains)
            except Exception:
                is_affiliate = False
        else:
            is_affiliate = True
        if is_affiliate: new_rels.add("sponsored")
        a["rel"] = " ".join(sorted(existing_rel.union(new_rels)))
        if not href or href in ("#","javascript:void(0)"): a.unwrap()
    html_text = str(soup)
    html_text = _linkify_bare_urls(html_text)
    return html_text

def autop(text_or_html: str) -> str:
    content = (text_or_html or "").strip()
    if not looks_like_html(content): content = markdown_to_html(content)
    return content

def normalize_post_html(text: str, affiliate_domains: Iterable[str] | None = None) -> str:
    content = autop(text)
    content = fix_affiliate_links(content, affiliate_domains=affiliate_domains)
    return content
