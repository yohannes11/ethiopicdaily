from django.contrib import admin

from .models import Article, Category, ReviewNote


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
