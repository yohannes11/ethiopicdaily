"""
Background scheduler that auto-fetches Telegram channels.

Runs every minute and fetches any channel whose fetch_interval has elapsed
since its last_fetched_at.  New messages are saved as pending TelegramImport
records (duplicates are silently skipped via get_or_create).
"""

import logging

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from django.utils import timezone

logger = logging.getLogger(__name__)

_scheduler = None


def _auto_fetch():
    """Periodic job: check each active channel and fetch if due."""
    try:
        from .models import TelegramChannel, TelegramImport
        from .services import fetch_telegram_messages

        channels = TelegramChannel.objects.filter(is_active=True)
        for ch in channels:
            if not ch.is_due():
                continue
            try:
                messages = fetch_telegram_messages(ch.slug, count=5)
            except Exception as exc:
                logger.warning("Auto-fetch failed for @%s: %s", ch.slug, exc)
                continue

            created = 0
            for item in messages:
                _, was_new = TelegramImport.objects.get_or_create(
                    message_id=item["message_id"],
                    defaults={
                        "channel":    item["channel"],
                        "source_url": item["source_url"],
                        "raw_text":   item["raw_text"],
                        "date":       item["date"],
                        "image_urls": item.get("image_urls", []),
                    },
                )
                if was_new:
                    created += 1

            ch.last_fetched_at = timezone.now()
            ch.save(update_fields=["last_fetched_at"])

            if created:
                logger.info("Auto-fetched %d new message(s) from @%s", created, ch.slug)
    except Exception as exc:
        logger.error("Error in auto-fetch job: %s", exc, exc_info=True)


def start():
    global _scheduler
    if _scheduler is not None:
        return  # already running

    _scheduler = BackgroundScheduler(timezone="UTC")
    _scheduler.add_job(
        _auto_fetch,
        trigger=IntervalTrigger(minutes=1),
        id="telegram_auto_fetch",
        replace_existing=True,
        max_instances=1,
        coalesce=True,
    )
    _scheduler.start()
    logger.info("Telegram auto-fetch scheduler started (runs every 1 minute).")


def stop():
    global _scheduler
    if _scheduler is not None:
        _scheduler.shutdown(wait=False)
        _scheduler = None
