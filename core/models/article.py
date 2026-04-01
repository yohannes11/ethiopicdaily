import re

from django.conf import settings
from django.db import models
from django.utils import timezone
from django.utils.text import slugify


class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(unique=True)
    color = models.CharField(
        max_length=30,
        default="red",
        help_text="Tailwind color name used for the category badge.",
    )

    class Meta:
        verbose_name_plural = "categories"
        ordering = ["name"]

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class Article(models.Model):
    class Status(models.TextChoices):
        DRAFT     = "draft",      "Draft"
        SUBMITTED = "submitted",  "Submitted for Review"
        IN_REVIEW = "in_review",  "In Review"
        PUBLISHED = "published",  "Published"
        REJECTED  = "rejected",   "Rejected"

    title       = models.CharField(max_length=255)
    slug        = models.SlugField(unique=True, max_length=255)
    summary     = models.TextField(max_length=500)
    content     = models.TextField()
    image_url   = models.URLField(blank=True)
    video_url   = models.URLField(blank=True, help_text="YouTube, Vimeo, or direct .mp4/.webm link")
    category    = models.ForeignKey(
        Category, on_delete=models.SET_NULL, null=True, blank=True,
        related_name="articles",
    )
    author      = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
        related_name="articles",
    )
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
        related_name="reviewed_articles",
    )

    status       = models.CharField(
        max_length=20, choices=Status.choices, default=Status.DRAFT, db_index=True
    )
    is_featured  = models.BooleanField(default=False, db_index=True)
    is_breaking  = models.BooleanField(default=False, db_index=True)
    views_count  = models.PositiveIntegerField(default=0)

    published_at  = models.DateTimeField(default=timezone.now)
    submitted_at  = models.DateTimeField(null=True, blank=True)
    reviewed_at   = models.DateTimeField(null=True, blank=True)
    created_at    = models.DateTimeField(auto_now_add=True)
    updated_at    = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-published_at"]

    def save(self, *args, **kwargs):
        if not self.slug:
            base = slugify(self.title) or f"article-{Article.objects.count() + 1}"
            slug, counter = base, 1
            while Article.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f"{base}-{counter}"
                counter += 1
            self.slug = slug
        super().save(*args, **kwargs)

    @property
    def embed_video_url(self):
        if not self.video_url:
            return None
        url = self.video_url.strip()
        yt = re.search(r'(?:youtube\.com/watch\?.*v=|youtu\.be/)([a-zA-Z0-9_-]{11})', url)
        if yt:
            return f'https://www.youtube.com/embed/{yt.group(1)}?rel=0'
        vimeo = re.search(r'vimeo\.com/(\d+)', url)
        if vimeo:
            return f'https://player.vimeo.com/video/{vimeo.group(1)}'
        if re.search(r'\.(mp4|webm|ogg|mov)(\?.*)?$', url, re.IGNORECASE):
            return url
        return None

    def reading_time(self) -> int:
        words = len(self.content.split())
        return max(1, round(words / 200))

    def can_edit(self, user) -> bool:
        """Writer can edit their own drafts/rejected articles. Admin can edit anything."""
        if user.is_admin():
            return True
        if user.is_writer() and self.author == user:
            return self.status in (self.Status.DRAFT, self.Status.REJECTED)
        return False

    def can_submit(self, user) -> bool:
        if user.is_admin():
            return self.status in (self.Status.DRAFT, self.Status.REJECTED)
        return (
            user.is_writer()
            and self.author == user
            and self.status in (self.Status.DRAFT, self.Status.REJECTED)
        )

    def can_withdraw(self, user) -> bool:
        if user.is_admin():
            return self.status == self.Status.SUBMITTED
        return (
            user.is_writer()
            and self.author == user
            and self.status == self.Status.SUBMITTED
        )

    def __str__(self):
        return self.title


class ReviewNote(models.Model):
    class Action(models.TextChoices):
        SUBMITTED = "submitted",  "Submitted"
        WITHDRAWN = "withdrawn",  "Withdrawn"
        IN_REVIEW = "in_review",  "Taken for Review"
        APPROVED  = "approved",   "Approved"
        REJECTED  = "rejected",   "Rejected"
        COMMENT   = "comment",    "Comment"

    article    = models.ForeignKey(Article, on_delete=models.CASCADE, related_name="review_notes")
    actor      = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
        related_name="review_notes",
    )
    action     = models.CharField(max_length=20, choices=Action.choices)
    note       = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]

    def __str__(self):
        return f"{self.action} — {self.article.title[:40]}"
