from django.db import models


class Advertisement(models.Model):
    class Placement(models.TextChoices):
        HOMEPAGE_BANNER  = 'homepage_banner',  'Homepage — Top Banner (728×90)'
        HOMEPAGE_SIDEBAR = 'homepage_sidebar', 'Homepage — Sidebar (300×250)'
        ARTICLE_TOP      = 'article_top',      'Article — After Image (responsive)'
        ARTICLE_BOTTOM   = 'article_bottom',   'Article — Above Related Stories (728×90)'

    name        = models.CharField(max_length=100, help_text="Internal label — not shown to readers.")
    client_name = models.CharField(
        max_length=150, blank=True,
        help_text="Name of the advertiser (e.g. 'Habesha Brewery'). Only visible to admins.",
    )
    placement   = models.CharField(max_length=30, choices=Placement.choices)

    # ── Option A: image-based personal ad ─────────────────────────
    image_url = models.URLField(
        blank=True,
        help_text="URL of the ad image (JPG/PNG/GIF/WebP). Use this for personal-connection ads.",
    )
    link_url  = models.URLField(
        blank=True,
        help_text="Where the ad links to when clicked.",
    )

    # ── Option B: raw HTML / Google AdSense ───────────────────────
    ad_code = models.TextField(
        blank=True,
        help_text="Paste a Google AdSense &lt;ins&gt; block, or any custom HTML. "
                  "Leave blank if using the image fields above.",
    )

    is_active  = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["placement", "-updated_at"]

    @property
    def rendered_html(self):
        """Return the HTML to inject into the ad slot.

        Priority: raw ad_code first (Google AdSense / custom HTML),
        then auto-build from image_url + link_url.
        """
        if self.ad_code:
            return self.ad_code
        if self.image_url:
            href   = self.link_url or '#'
            alt    = self.client_name or self.name
            return (
                f'<a href="{href}" target="_blank" rel="noopener sponsored" '
                f'style="display:block;text-align:center;">'
                f'<img src="{self.image_url}" alt="{alt}" '
                f'style="max-width:100%;height:auto;display:inline-block;" loading="lazy">'
                f'</a>'
            )
        return ''

    def __str__(self):
        status = "active" if self.is_active else "paused"
        return f"{self.name} [{self.get_placement_display()}] ({status})"