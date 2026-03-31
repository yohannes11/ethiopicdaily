"""
Template context processors for the core app.
"""

from .models import TelegramChannel


def telegram_channels(request):
    """
    Inject active TelegramChannel objects into every template context.
    Used by the CMS sidebar to list channels dynamically.
    """
    channels = TelegramChannel.objects.filter(is_active=True)
    return {"telegram_channels": channels}
