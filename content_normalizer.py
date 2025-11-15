# ======================================================================
# File: content_normalizer.py  (FINAL FIXED VERSION)
# ======================================================================
from __future__ import annotations

import html
import re
from typing import Iterable
from urllib.parse import urlparse

from bs4 import BeautifulSoup
from markdown import markdown


# Detect minimal HTML (avoid false positives)
_HTML_HINT_RE = re.compile(
    r"</?(p|h[1-6]|a|ul|ol|li|strong|em|blockquote|img|figure)\b",
    re.I,
)

_SMART_QUOTES = {
    "\u201C": '"', "\u201D": '"', "\u201E": '"', "\u201F": '"',
    "\u2018": "'", "\u2019": "'", "\u2032": "'", "\u2033": '"',
}

# Markdown-style links: [label](url "title")
_MD_LINK_RE = re.compile(
    r"\[([^\]]+)\]\(([^)\s]+)(?:\s+\"([^\"]+)\")?\)",
    re.MULTILINE,
)

# Bare URLs: https://x.com or www.x.com
_URL_RE = re.compile(
    r'(?P<pre>^|[\s>])(?P<url>(?:https?://|www\.)[^\s<]+)',
    re.IGNORECASE,
)


# ----------------------------------------------------------------------
# Helpers
# ----------------------------------------------------------------------
def _unsmart(s: str) -> str:
    return "".join(_SMART_QUOTES.get(ch, ch) for ch in s)


def _ensure_scheme(url: str) -> str:
    if not url:
        return url
    parsed = urlparse(url)

    # Already has scheme
    if parsed.scheme:
        return url

    # Protocol-relative: //example.com
    if url.startswith("//"):
        return f"https:{url}"

    # Do not modify special pseudo-schemes
    if url.startswith(("mailto:", "tel:", "#", "javascript:")):
        return url

    # Add https by default
    return f"https://{url}"


# ----------------------------------------------------------------------
# Markdown Conversion
# ----------------------------------------------------------------------
def markdown_to_html(md_text: str) -> str:
    """Convert Markdown to HTML; ensures proper <p>/<h*> structure."""
    text = (md_text or "").replace("\r\n", "\n").replace("\r", "\n").strip()

    # SECURITY FIX: Remove raw HTML inside Markdown before markdown() expansion
    text = re.sub(r"<(script|style)[^>]*>.*?</\1>", "", text, flags=re.DOTALL | re.I)

    return markdown(text, extensions=["extra", "sane_lists", "attr_list"])


# ----------------------------------------------------------------------
# Link Normalization
# ----------------------------------------------------------------------
def _convert_md_links_in_htmlish(text: str) -> str:
    """Convert Markdown links inside HTML-ish input."""

    def _repl(m: re.Match) -> str:
        label, href, title = m.group(1), m.group(2), m.group(3)
        href = _ensure_scheme(_unsmart(href.strip()))
        title_attr = f' title="{html.escape(title)}"' if title else ""
        return (
            f'<a href="{html.escape(href, quote=True)}"{title_attr}>'
            f'{html.escape(label)}</a>'
        )

    return _MD_LINK_RE.sub(_repl, text)


def _linkify_bare_urls(html_text: str) -> str:
    """Convert raw http(s)/www links into <a> tags."""

    def _repl(m: re.Match) -> str:
        pre = m.group("pre")
        url = m.group("url")
        href = _ensure_scheme(url)
        return (
            f'{pre}<a href="{html.escape(href, quote=True)}" '
            f'target="_blank" rel="nofollow noopener sponsored">'
            f'{html.escape(url)}</a>'
        )

    return _URL_RE.sub(_repl, html_text)


# ----------------------------------------------------------------------
# HTML detection
# ----------------------------------------------------------------------
def looks_like_html(text: str) -> bool:
    return bool(_HTML_HINT_RE.search(text or ""))


# ----------------------------------------------------------------------
# Affiliate Link Hardening
# ----------------------------------------------------------------------
def fix_affiliate_links(html_text: str, affiliate_domains: Iterable[str] | None = None) -> str:
    """
    Harden outbound links:
      - Ensure scheme
      - Ensure rel="nofollow noopener sponsored"
      - Ensure target="_blank"
    """
    if not html_text:
        return html_text

    # Convert Markdown links inside HTML-ish text
    html_text = _convert_md_links_in_htmlish(html_text)

    soup = BeautifulSoup(html_text, "html.parser")

    for a in soup.find_all("a"):
        href = _ensure_scheme(_unsmart((a.get("href") or "").strip()))
        if href:
            a["href"] = href

        # Always open in new tab
        a["target"] = "_blank"

        # Collect existing rel attributes
        existing_rel = set(a.get("rel", []))
        rels = {"nofollow", "noopener"}

        # Affiliate detection
        is_affiliate = False
        if affiliate_domains:
            try:
                host = urlparse(href).netloc.lower()
                is_affiliate = any(host.endswith(d.lower()) for d in affiliate_domains)
            except:
                is_affiliate = False
        else:
            # Default: treat ALL external links as affiliate
            is_affiliate = True

        if is_affiliate:
            rels.add("sponsored")

        # Rebuild rel=
        a["rel"] = " ".join(sorted(existing_rel | rels))

        # Remove dead links
        if not href or href in ("#", "javascript:void(0)"):
            a.unwrap()

    # Convert back to string
    html_text = str(soup)

    # Linkify remaining plain URLs
    html_text = _linkify_bare_urls(html_text)

    return html_text


# ----------------------------------------------------------------------
# HTML Autop
# ----------------------------------------------------------------------
def autop(text_or_html: str) -> str:
    """
    Guarantee HTML output with proper paragraphs if needed.
    """
    content = (text_or_html or "").strip()
    if not looks_like_html(content):
        content = markdown_to_html(content)
    return content


# ----------------------------------------------------------------------
# MAIN: Normalize article body
# ----------------------------------------------------------------------
def normalize_post_html(text: str, affiliate_domains: Iterable[str] | None = None) -> str:
    content = autop(text)
    content = fix_affiliate_links(content, affiliate_domains=affiliate_domains)
    return content
