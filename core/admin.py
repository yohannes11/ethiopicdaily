from django.contrib import admin
from django.contrib.admin import AdminSite
from django.db.models import Q
from django.shortcuts import render
from django.urls import path

from .models import Article, Category, ReviewNote, TelegramChannel, TelegramImport


# ---------------------------------------------------------------------------
# Global search view
# ---------------------------------------------------------------------------

ALL_TYPES = ["articles", "categories", "users", "channels", "imports"]


def global_search_view(request):
    from datetime import datetime
    from users.models import User

    query = request.GET.get("q", "").strip()
    date_from = request.GET.get("date_from", "").strip()
    date_to = request.GET.get("date_to", "").strip()
    selected_types = request.GET.getlist("types") or ALL_TYPES

    results = {}
    total = 0

    # Parse dates; ignore malformed values
    try:
        dt_from = datetime.strptime(date_from, "%Y-%m-%d") if date_from else None
    except ValueError:
        dt_from = None
    try:
        dt_to = datetime.strptime(date_to, "%Y-%m-%d") if date_to else None
    except ValueError:
        dt_to = None

    if query:
        if "articles" in selected_types:
            qs = Article.objects.filter(
                Q(title__icontains=query) | Q(summary__icontains=query) | Q(content__icontains=query)
            ).select_related("category", "author").order_by("-created_at")
            if dt_from:
                qs = qs.filter(created_at__date__gte=dt_from.date())
            if dt_to:
                qs = qs.filter(created_at__date__lte=dt_to.date())
            results["Articles"] = ("core_article_change", list(qs[:20]))

        if "categories" in selected_types:
            qs = Category.objects.filter(Q(name__icontains=query) | Q(slug__icontains=query))
            results["Categories"] = ("core_category_change", list(qs[:10]))

        if "users" in selected_types:
            qs = User.objects.filter(
                Q(email__icontains=query) | Q(username__icontains=query)
                | Q(first_name__icontains=query) | Q(last_name__icontains=query)
            )
            if dt_from:
                qs = qs.filter(date_joined__date__gte=dt_from.date())
            if dt_to:
                qs = qs.filter(date_joined__date__lte=dt_to.date())
            results["Users"] = ("users_user_change", list(qs[:10]))

        if "channels" in selected_types:
            qs = TelegramChannel.objects.filter(
                Q(display_name__icontains=query) | Q(slug__icontains=query)
            )
            if dt_from:
                qs = qs.filter(created_at__date__gte=dt_from.date())
            if dt_to:
                qs = qs.filter(created_at__date__lte=dt_to.date())
            results["Telegram Channels"] = ("core_telegramchannel_change", list(qs[:10]))

        if "imports" in selected_types:
            qs = TelegramImport.objects.filter(
                Q(raw_text__icontains=query) | Q(message_id__icontains=query)
            ).select_related("channel")
            if dt_from:
                qs = qs.filter(fetched_at__date__gte=dt_from.date())
            if dt_to:
                qs = qs.filter(fetched_at__date__lte=dt_to.date())
            results["Telegram Imports"] = ("core_telegramimport_change", list(qs[:10]))

        total = sum(len(v) for _, v in results.values())

    context = {
        **admin.site.each_context(request),
        "query": query,
        "date_from": date_from,
        "date_to": date_to,
        "selected_types": selected_types,
        "all_types": ALL_TYPES,
        "results": results,
        "total": total,
        "title": "Global Search",
    }
    return render(request, "admin/global_search.html", context)


# Patch the admin site to include the global search URL
class _SearchableAdminSite(AdminSite):
    def get_urls(self):
        urls = super().get_urls()
        return [path("search/", self.admin_view(global_search_view), name="global_search")] + urls


admin.site.__class__ = _SearchableAdminSite


# ---------------------------------------------------------------------------
# Model admins
# ---------------------------------------------------------------------------


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "color")
    prepopulated_fields = {"slug": ("name",)}
    search_fields = ("name", "slug")


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
