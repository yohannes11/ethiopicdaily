from django.db import migrations, models


def seed_channels(apps, schema_editor):
    TelegramChannel = apps.get_model("core", "TelegramChannel")
    TelegramChannel.objects.get_or_create(
        slug="tikvahethiopia",
        defaults={"display_name": "Tikvah Ethiopia", "fetch_interval": 5, "is_active": True},
    )
    TelegramChannel.objects.get_or_create(
        slug="ayuzehabeshanews",
        defaults={"display_name": "Ayuze Habesh News", "fetch_interval": 5, "is_active": True},
    )


def unseed_channels(apps, schema_editor):
    TelegramChannel = apps.get_model("core", "TelegramChannel")
    TelegramChannel.objects.filter(
        slug__in=["tikvahethiopia", "ayuzehabeshanews"]
    ).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0006_telegramimport_channel"),
    ]

    operations = [
        migrations.CreateModel(
            name="TelegramChannel",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("slug", models.SlugField(max_length=100, unique=True)),
                ("display_name", models.CharField(max_length=200)),
                ("is_active", models.BooleanField(db_index=True, default=True)),
                ("fetch_interval", models.PositiveIntegerField(
                    default=5,
                    help_text="How often (in minutes) to auto-fetch. Minimum 1.",
                )),
                ("last_fetched_at", models.DateTimeField(blank=True, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
            ],
            options={
                "ordering": ["display_name"],
            },
        ),
        migrations.RunPython(seed_channels, reverse_code=unseed_channels),
    ]
