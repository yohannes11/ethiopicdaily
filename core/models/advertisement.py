from django.db import models


class Advertisement(models.Model):
    class Placement(models.TextChoices):
        HOMEPAGE_BANNER  = 'homepage_banner',  'Homepage — Top Banner (728×90)'
        HOMEPAGE_SIDEBAR = 'homepage_sidebar', 'Homepage — Sidebar (300×250)'
        ARTICLE_TOP      = 'article_top',      'Article — After Image (responsive)'
        ARTICLE_BOTTOM   = 'article_bottom',   'Article — Above Related Stories (728×90)'

    name      = models.CharField(max_length=100, help_text="Internal label — not shown to readers.")
    placement = models.CharField(max_length=30, choices=Placement.choices)
    ad_code   = models.TextField(
        help_text="Paste your Google AdSense &lt;ins&gt; block or any HTML ad code here."
    )
    is_active  = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["placement", "-updated_at"]

    def __str__(self):
        status = "active" if self.is_active else "paused"
        return f"{self.name} [{self.get_placement_display()}] ({status})"