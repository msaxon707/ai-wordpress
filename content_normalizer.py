# ======================================================================
# File: content_normalizer.py
# Path: ./content_normalizer.py
# Purpose: Convert AI output to clean, WP-ready HTML; harden affiliate links
# ======================================================================
from __future__ import annotations

import html
import re
from typing import Iterable
from urllib.parse import urlparse

from bs4 import BeautifulSoup
from markdown import markdown


_HTML_HINT_RE = re.compile(r"</?(p|h[1-6]|a|ul|ol|li|strong|em|blockquote|img|figure)\b", re.I)
_SMART_QUOTES = {
    "\u201C": '"', "\u201D": '"', "\u201E": '"', "\u201F": '"',
    "\u2018": "'", "\u2019": "'", "\u2032": "'", "\u2033": '"',
}
_MD_LINK_RE = re.compile(r"\[([^\]]+)\]\(([^)\s]+)(?:\s+\"([^\"]+)\")?\)", re.MULTILINE)
_URL_RE = re.compile(r'(?P<pre>^|[\s>])(?P<url>(?:https?://|www\.)[^\s<]+)', re.IGNORECASE)


def _unsmart(s: str) -> str:
    return "".join(_SMART_QUOTES.get(ch, ch) for ch in s)


def _ensure_scheme(url: str) -> str:
    if not url:
        return url
    parsed = urlparse(url)
    if not parsed.scheme:
        if url.startswith("//"):
            return f"https:{url}"
        if url.startswith(("mailto:", "tel:", "#")):
            return url
        return f"https://{url}"
    return url


def markdown_to_html(md_text: str) -> str:
    """
    Convert Markdown to HTML with sane defaults.
    Why: Prevents literal '#' from rendering; produces proper <h*> and <p>.
    """
    text = (md_text or "").replace("\r\n", "\n").replace("\r", "\n").strip()
    return markdown(text, extensions=["extra", "sane_lists", "attr_list"])


def _convert_md_links_in_htmlish(text: str) -> str:
    def _repl(m: re.Match) -> str:
        label, href, title = m.group(1), m.group(2), m.group(3)
        href = _ensure_scheme(_unsmart(href.strip()))
        title_attr = f' title="{html.escape(title)}"' if title else ""
        return f'<a href="{html.escape(href, quote=True)}"{title_attr}>{html.escape(label)}</a>'
    return _MD_LINK_RE.sub(_repl, text)


def _linkify_bare_urls(html_text: str) -> str:
    def _repl(m: re.Match) -> str:
        pre = m.group("pre")
        url = m.group("url")
        href = _ensure_scheme(url)
        return f'{pre}<a href="{html.escape(href, quote=True)}" target="_blank" rel="nofollow noopener sponsored">{html.escape(url)}</a>'
    return _URL_RE.sub(_repl, html_text)


def looks_like_html(text: str) -> bool:
    return bool(_HTML_HINT_RE.search(text or ""))


def fix_affiliate_links(html_text: str, affiliate_domains: Iterable[str] | None = None) -> str:
    """
    Ensure <a> tags are valid/clickable and carry proper rel/target flags.
    Why: Affiliate networks require sponsored/nofollow; broken links silently hurt revenue.
    """
    if not html_text:
        return html_text

    html_text = _convert_md_links_in_htmlish(html_text)

    soup = BeautifulSoup(html_text, "html.parser")

    for a in soup.find_all("a"):
        href = _ensure_scheme(_unsmart((a.get("href") or "").strip()))
        if href:
            a["href"] = href

        a["target"] = "_blank"

        existing_rel = set((a.get("rel") or []))
        new_rels = {"nofollow", "noopener"}

        is_affiliate = False
        if affiliate_domains:
            try:
                host = urlparse(href).netloc.lower()
                is_affiliate = any(host.endswith(d.lower()) for d in affiliate_domains)
            except Exception:
                is_affiliate = False
        else:
            is_affiliate = True

        if is_affiliate:
            new_rels.add("sponsored")

        a["rel"] = " ".join(sorted(existing_rel.union(new_rels)))

        if not href or href in ("#", "javascript:void(0)"):
            a.unwrap()

    html_text = str(soup)
    html_text = _linkify_bare_urls(html_text)
    return html_text


def autop(text_or_html: str) -> str:
    """
    Convert to HTML if needed; guarantees proper <p>/<h*> structure.
    """
    content = (text_or_html or "").strip()
    if not looks_like_html(content):
        content = markdown_to_html(content)
    return content


def normalize_post_html(text: str, affiliate_domains: Iterable[str] | None = None) -> str:
    """
    Main entry: normalize headings/paragraphs and harden links.
    """
    content = autop(text)
    content = fix_affiliate_links(content, affiliate_domains=affiliate_domains)
    return content
