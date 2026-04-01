"""
Template context processors for the core app.
"""
from .models import Advertisement, Article, Category, TelegramChannel


def telegram_channels(request):
    """
    Inject active TelegramChannel objects into every template context.
    Used by the CMS sidebar to list channels dynamically.
    """
    return {
        "telegram_channels": TelegramChannel.objects.filter(is_active=True).only("slug", "display_name"),
    }


def global_context(request):
    """
    Inject site-wide variables needed by the public base template:
    all categories (for the header nav) and the current breaking article
    (for the ticker).
    """
    breaking = (
        Article.objects
        .filter(status=Article.Status.PUBLISHED, is_breaking=True)
        .only("title", "slug")
        .first()
    )
    return {
        "categories": Category.objects.all(),
        "breaking": breaking,
    }


def active_ads(request):
    """
    Inject active advertisements keyed by placement into every template context.
    Only one ad per placement slot is served (the most recently updated active one).
    Usage in templates: {{ ads.homepage_banner.ad_code|safe }}
    """
    ads = Advertisement.objects.filter(is_active=True)
    ads_map = {}
    for ad in ads:
        # First active ad per placement wins
        if ad.placement not in ads_map:
            ads_map[ad.placement] = ad
    return {"ads": ads_map}
