from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0005_telegramimport_image_urls'),
    ]

    operations = [
        migrations.AddField(
            model_name='telegramimport',
            name='channel',
            field=models.CharField(db_index=True, default='tikvahethiopia', max_length=100),
        ),
    ]
