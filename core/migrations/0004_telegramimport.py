from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0003_add_video_url_and_reactions'),
    ]

    operations = [
        migrations.CreateModel(
            name='TelegramImport',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('message_id', models.CharField(max_length=100, unique=True)),
                ('source_url', models.URLField(blank=True)),
                ('raw_text', models.TextField()),
                ('date', models.DateTimeField()),
                ('fetched_at', models.DateTimeField(auto_now_add=True)),
                ('status', models.CharField(
                    choices=[('pending', 'Pending Review'), ('approved', 'Approved'), ('rejected', 'Rejected')],
                    db_index=True, default='pending', max_length=20,
                )),
                ('article', models.OneToOneField(
                    blank=True, null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='telegram_import',
                    to='core.article',
                )),
            ],
            options={
                'ordering': ['-date'],
            },
        ),
    ]
