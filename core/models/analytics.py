from django.db import models


class PageView(models.Model):
    path        = models.CharField(max_length=500, db_index=True)
    user        = models.ForeignKey(
        'users.User',
        null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name='page_views',
    )
    session_key = models.CharField(max_length=100, blank=True, db_index=True)
    date        = models.DateField(auto_now_add=True, db_index=True)
    created_at  = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['date', 'path']),
        ]

    def __str__(self):
        return f"{self.path} — {self.date}"