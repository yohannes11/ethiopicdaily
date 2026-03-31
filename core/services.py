"""
Telegram channel scraper.

Fetches the latest messages from public Telegram channels using
the public web preview endpoint (no API key required).
"""

import re
import unicodedata

import requests
from bs4 import BeautifulSoup
from django.utils.dateparse import parse_datetime
from django.utils import timezone


HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9",
}


# ── Text cleaning ─────────────────────────────────────────────────────────────

def clean_text(text: str) -> str:
    """
    Remove emojis, symbols, and formatting noise from scraped Telegram text.

    Keeps:  letters, numbers, punctuation, whitespace (all Unicode scripts,
            so Amharic/Arabic/etc. are preserved).
    Strips: emoji, pictographs, dingbats, zero-width chars, variation selectors,
            control characters, and other non-printable symbols.
    """
    result = []
    for ch in text:
        cat = unicodedata.category(ch)
        cp  = ord(ch)

        # Skip zero-width / invisible / control characters
        if cat in ("Cf", "Cc", "Cs"):
            continue

        # Skip Unicode variation selectors (U+FE00–FE0F, U+E0100–E01EF)
        if 0xFE00 <= cp <= 0xFE0F or 0xE0100 <= cp <= 0xE01EF:
            continue

        # Skip emoji and symbol blocks
        # So (Symbol, other) covers most emoji; also catch specific ranges
        if cat == "So":
            continue

        # Common emoji ranges not always classified as So
        if (
            0x1F600 <= cp <= 0x1F64F   # emoticons
            or 0x1F300 <= cp <= 0x1F5FF  # misc symbols & pictographs
            or 0x1F680 <= cp <= 0x1F6FF  # transport & map
            or 0x1F700 <= cp <= 0x1F77F  # alchemical symbols
            or 0x1F780 <= cp <= 0x1F7FF  # geometric shapes extended
            or 0x1F800 <= cp <= 0x1F8FF  # supplemental arrows
            or 0x1F900 <= cp <= 0x1F9FF  # supplemental symbols
            or 0x1FA00 <= cp <= 0x1FA6F  # chess symbols
            or 0x1FA70 <= cp <= 0x1FAFF  # symbols and pictographs extended-A
            or 0x2600  <= cp <= 0x26FF   # misc symbols
            or 0x2700  <= cp <= 0x27BF   # dingbats
            or 0xFE00  <= cp <= 0xFE0F   # variation selectors
            or 0x200B  <= cp <= 0x200F   # zero-width spaces etc.
            or 0x2060  <= cp <= 0x206F   # word joiner etc.
        ):
            continue

        result.append(ch)

    cleaned = "".join(result)
    # Collapse runs of blank lines to at most one blank line
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)
    # Strip trailing whitespace on each line
    cleaned = "\n".join(line.rstrip() for line in cleaned.splitlines())
    return cleaned.strip()


# ── Channel helpers ───────────────────────────────────────────────────────────

def get_active_channels() -> dict[str, str]:
    """
    Return {slug: display_name} for all active TelegramChannel records.
    Falls back to an empty dict if the table doesn't exist yet (e.g. during migrations).
    """
    try:
        from .models import TelegramChannel
        return {ch.slug: ch.display_name for ch in TelegramChannel.objects.filter(is_active=True)}
    except Exception:
        return {}


# ── Scraping ──────────────────────────────────────────────────────────────────

def fetch_telegram_messages(channel: str, count: int = 5) -> list[dict]:
    """
    Scrape the last `count` messages from a public Telegram channel.

    Args:
        channel: Telegram username (must exist as an active TelegramChannel).
        count:   Maximum number of messages to return.

    Returns a list of dicts:
        {
            "message_id": str,         e.g. "tikvahethiopia/1234"
            "channel":    str,         channel slug
            "source_url": str,
            "raw_text":   str,         cleaned — no emojis or symbols
            "date":       datetime (timezone-aware),
            "image_urls": list[str],
        }

    Raises:
        ValueError: if `channel` is not an active channel in the DB.
        requests.RequestException: on network/HTTP errors.
    """
    active = get_active_channels()
    if channel not in active:
        raise ValueError(f"Unknown or inactive channel '{channel}'.")

    url      = f"https://t.me/s/{channel}"
    response = requests.get(url, headers=HEADERS, timeout=15)
    response.raise_for_status()

    soup             = BeautifulSoup(response.text, "html.parser")
    message_wrappers = soup.select(".tgme_widget_message")

    results = []
    for msg in message_wrappers[-count:]:
        data_post = msg.get("data-post", "").strip()
        if not data_post:
            continue

        text_el  = msg.select_one(".tgme_widget_message_text")
        if not text_el:
            continue
        raw_text = clean_text(text_el.get_text(separator="\n").strip())
        if not raw_text:
            continue

        time_el  = msg.select_one("time[datetime]")
        date_str = time_el["datetime"] if time_el else None
        date     = parse_datetime(date_str) if date_str else None
        if date is None:
            date = timezone.now()
        elif timezone.is_naive(date):
            date = timezone.make_aware(date)

        image_urls = []
        for photo_wrap in msg.select(".tgme_widget_message_photo_wrap"):
            style = photo_wrap.get("style", "")
            m = re.search(r"background-image:url\('([^']+)'\)", style)
            if m:
                image_urls.append(m.group(1))
        for img in msg.select(".tgme_widget_message_photo img"):
            src = img.get("src", "")
            if src and src not in image_urls:
                image_urls.append(src)

        results.append(
            {
                "message_id": data_post,
                "channel":    channel,
                "source_url": f"https://t.me/{data_post}",
                "raw_text":   raw_text,
                "date":       date,
                "image_urls": image_urls,
            }
        )

    return results


def fetch_all_channels(count_per_channel: int = 5) -> dict[str, list[dict] | Exception]:
    """
    Fetch messages from every active registered channel.

    Returns a dict mapping channel slug → list of message dicts (or the
    Exception raised if that channel failed to load).
    """
    results = {}
    for channel in get_active_channels():
        try:
            results[channel] = fetch_telegram_messages(channel, count=count_per_channel)
        except Exception as exc:  # noqa: BLE001
            results[channel] = exc
    return results
