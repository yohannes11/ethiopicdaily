from django.contrib import admin

from .models import Article, Category, ReviewNote, TelegramChannel, TelegramImport


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "color")
    prepopulated_fields = {"slug": ("name",)}


@admin.register(Article)
class ArticleAdmin(admin.ModelAdmin):
    list_display  = ("title", "category", "author", "status", "is_featured", "is_breaking", "published_at")
    list_filter   = ("status", "category", "is_featured", "is_breaking")
    list_editable = ("status", "is_featured", "is_breaking")
    search_fields = ("title", "summary", "content")
    prepopulated_fields = {"slug": ("title",)}
    date_hierarchy = "published_at"
    ordering = ("-published_at",)
    readonly_fields = ("submitted_at", "reviewed_at", "reviewed_by", "created_at", "updated_at")


@admin.register(ReviewNote)
class ReviewNoteAdmin(admin.ModelAdmin):
    list_display  = ("article", "actor", "action", "created_at")
    list_filter   = ("action",)
    search_fields = ("article__title", "actor__email", "note")
    readonly_fields = ("created_at",)


@admin.register(TelegramChannel)
class TelegramChannelAdmin(admin.ModelAdmin):
    list_display  = ("display_name", "slug", "is_active", "fetch_interval", "last_fetched_at")
    list_filter   = ("is_active",)
    list_editable = ("is_active", "fetch_interval")
    search_fields = ("display_name", "slug")
    readonly_fields = ("created_at", "last_fetched_at")


@admin.register(TelegramImport)
class TelegramImportAdmin(admin.ModelAdmin):
    list_display  = ("message_id", "channel", "status", "date", "fetched_at")
    list_filter   = ("status", "channel")
    search_fields = ("message_id", "raw_text")
    readonly_fields = ("message_id", "channel", "source_url", "raw_text", "image_urls", "date", "fetched_at")
    list_select_related = ("article",)
