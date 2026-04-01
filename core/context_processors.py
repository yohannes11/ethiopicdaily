"""
Template context processors for the core app.
"""
from .models import Article, Category, TelegramChannel


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
