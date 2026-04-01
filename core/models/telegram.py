from django.db import models
from django.utils import timezone


class TelegramChannel(models.Model):
    slug         = models.SlugField(max_length=100, unique=True)  # Telegram username
    display_name = models.CharField(max_length=200)
    is_active    = models.BooleanField(default=True, db_index=True)
    fetch_interval = models.PositiveIntegerField(
        default=5,
        help_text="How often (in minutes) to auto-fetch. Minimum 1.",
    )
    last_fetched_at = models.DateTimeField(null=True, blank=True)
    created_at      = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["display_name"]

    def __str__(self):
        return self.display_name

    def is_due(self):
        """Return True if it's time to fetch this channel again."""
        if not self.last_fetched_at:
            return True
        delta = timezone.now() - self.last_fetched_at
        return delta.total_seconds() >= self.fetch_interval * 60


class TelegramImport(models.Model):
    class Status(models.TextChoices):
        PENDING  = "pending",  "Pending Review"
        APPROVED = "approved", "Approved"
        REJECTED = "rejected", "Rejected"

    message_id  = models.CharField(max_length=100, unique=True)  # e.g. "tikvahethiopia/1234"
    channel     = models.CharField(max_length=100, default="tikvahethiopia", db_index=True)
    source_url  = models.URLField(blank=True)
    raw_text    = models.TextField()
    image_urls  = models.JSONField(default=list, blank=True)
    date        = models.DateTimeField()
    fetched_at  = models.DateTimeField(auto_now_add=True)
    status      = models.CharField(
        max_length=20, choices=Status.choices, default=Status.PENDING, db_index=True
    )
    article = models.OneToOneField(
        "core.Article", null=True, blank=True, on_delete=models.SET_NULL,
        related_name="telegram_import",
    )

    class Meta:
        ordering = ["-date"]

    def __str__(self):
        return f"TG:{self.message_id} ({self.status})"

    @property
    def suggested_title(self):
        for line in self.raw_text.splitlines():
            line = line.strip()
            if line:
                return line[:200]
        return "Untitled"

    @property
    def suggested_summary(self):
        lines = [l.strip() for l in self.raw_text.splitlines() if l.strip()]
        return " ".join(lines[:3])[:500]
