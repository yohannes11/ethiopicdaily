from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0004_telegramimport'),
    ]

    operations = [
        migrations.AddField(
            model_name='telegramimport',
            name='image_urls',
            field=models.JSONField(blank=True, default=list),
        ),
    ]
