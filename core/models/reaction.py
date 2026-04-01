from django.conf import settings
from django.db import models


class Reaction(models.Model):
    class Type(models.TextChoices):
        LIKE    = "like",    "👍 Like"
        LOVE    = "love",    "❤️ Love"
        WOW     = "wow",     "😮 Wow"
        SAD     = "sad",     "😢 Sad"
        ANGRY   = "angry",   "😡 Angry"

    article       = models.ForeignKey(
        "core.Article", on_delete=models.CASCADE, related_name="reactions"
    )
    user          = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="reactions"
    )
    reaction_type = models.CharField(max_length=10, choices=Type.choices)
    created_at    = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = [("article", "user")]

    def __str__(self):
        return f"{self.reaction_type} on {self.article.title[:40]}"
