from functools import wraps

from django.contrib import messages
from django.db import models
from django.http import Http404, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_POST

from .models import Article, Category, Reaction, ReviewNote, TelegramChannel, TelegramImport
from users.models import User

# ─────────────────────────────────────────────
# Permission decorators
# ─────────────────────────────────────────────

def _redirect_to_login(request):
    return redirect(f"{reverse('users:login')}?next={request.path}")


def writer_required(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return _redirect_to_login(request)
        if not (request.user.is_writer() or request.user.is_admin()):
            messages.error(request, "You need a writer or admin account to access the newsroom.")
            return redirect("core:homepage")
        return view_func(request, *args, **kwargs)
    return wrapper


def reviewer_required(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return _redirect_to_login(request)
        if not (request.user.is_reviewer() or request.user.is_admin()):
            messages.error(request, "You need a reviewer or admin account to access the review queue.")
            return redirect("core:homepage")
        return view_func(request, *args, **kwargs)
    return wrapper


def cms_required(view_func):
    """Any authenticated user with a CMS role (writer, reviewer, admin)."""
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return _redirect_to_login(request)
        return view_func(request, *args, **kwargs)
    return wrapper


def admin_required(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return _redirect_to_login(request)
        if not request.user.is_admin():
            messages.error(request, "Only admins can access this page.")
            return redirect("core:homepage")
        return view_func(request, *args, **kwargs)
    return wrapper


# ─────────────────────────────────────────────
# Public views
# ─────────────────────────────────────────────

def homepage(request):
    published = Article.objects.filter(status=Article.Status.PUBLISHED).select_related("category", "author")

    featured  = published.filter(is_featured=True).first()
    breaking  = published.filter(is_breaking=True).first()

    exclude_pk = featured.pk if featured else 0
    sub_hero   = published.exclude(pk=exclude_pk).order_by("-published_at")[:3]

    exclude_pks = [exclude_pk] + [a.pk for a in sub_hero]
    latest = published.exclude(pk__in=exclude_pks).order_by("-published_at")[:8]

    trending  = published.order_by("-views_count")[:6]
    most_read = published.order_by("-views_count")[:5]
    categories = Category.objects.all()

    category_sections = []
    for cat in categories[:4]:
        articles = list(published.filter(category=cat).order_by("-published_at")[:4])
        if articles:
            category_sections.append({"category": cat, "articles": articles})

    return render(request, "core/home.html", {
        "featured": featured,
        "breaking": breaking,
        "sub_hero": sub_hero,
        "latest": latest,
        "trending": trending,
        "most_read": most_read,
        "categories": categories,
        "category_sections": category_sections,
    })


def article_detail(request, slug):
    article = get_object_or_404(Article.objects.select_related("category", "author"), slug=slug)

    # Non-published articles: only visible to the author, reviewers, and admins.
    if article.status != Article.Status.PUBLISHED:
        if not request.user.is_authenticated:
            raise Http404
        if not (
            request.user == article.author
            or request.user.is_reviewer()
            or request.user.is_admin()
        ):
            raise Http404

    cookie_key = f"va_{article.pk}"
    already_viewed = request.COOKIES.get(cookie_key)
    if not already_viewed:
        Article.objects.filter(pk=article.pk).update(views_count=models.F("views_count") + 1)

    related = (
        Article.objects.filter(category=article.category, status=Article.Status.PUBLISHED)
        .exclude(pk=article.pk)
        .order_by("-published_at")[:3]
    )

    can_edit = request.user.is_authenticated and article.can_edit(request.user)

    reaction_counts = {r.value: 0 for r in Reaction.Type}
    for r in article.reactions.values("reaction_type").annotate(n=models.Count("id")):
        reaction_counts[r["reaction_type"]] = r["n"]

    user_reaction = None
    if request.user.is_authenticated:
        existing = article.reactions.filter(user=request.user).first()
        if existing:
            user_reaction = existing.reaction_type

    response = render(request, "core/article_detail.html", {
        "article": article,
        "related": related,
        "can_edit": can_edit,
        "reaction_counts": reaction_counts,
        "user_reaction": user_reaction,
        "reaction_types": Reaction.Type,
    })
    if not already_viewed:
        response.set_cookie(cookie_key, "1", max_age=30 * 24 * 60 * 60, httponly=True, samesite="Lax")
    return response


# ─────────────────────────────────────────────
# Editorial views  (writers + admins)
# ─────────────────────────────────────────────

@writer_required
def editorial_dashboard(request):
    if request.user.is_admin():
        qs = Article.objects.select_related("category", "author").order_by("-updated_at")
    else:
        qs = Article.objects.filter(author=request.user).select_related("category").order_by("-updated_at")

    status_filter = request.GET.get("status", "")
    if status_filter and status_filter in Article.Status.values:
        qs = qs.filter(status=status_filter)

    counts = {}
    base = Article.objects.filter(author=request.user) if not request.user.is_admin() else Article.objects
    for s in Article.Status:
        counts[s.value] = base.filter(status=s).count()

    seven_days_ago = timezone.now() - timezone.timedelta(days=7)
    extra = {}
    if request.user.is_admin():
        extra["total_users"] = User.objects.count()
        extra["recent_published"] = Article.objects.filter(
            status=Article.Status.PUBLISHED, updated_at__gte=seven_days_ago
        ).count()
        extra["telegram_pending"] = TelegramImport.objects.filter(
            status=TelegramImport.Status.PENDING
        ).count()

    return render(request, "core/editorial_dashboard.html", {
        "articles": qs,
        "status_choices": Article.Status.choices,
        "current_status": status_filter,
        "counts": counts,
        **extra,
    })


@writer_required
def article_create(request):
    categories = Category.objects.all()
    errors = {}
    form_data = {}

    if request.method == "POST":
        form_data = request.POST
        title     = request.POST.get("title", "").strip()
        summary   = request.POST.get("summary", "").strip()
        content   = request.POST.get("content", "").strip()
        cat_id    = request.POST.get("category", "").strip()
        image_url = request.POST.get("image_url", "").strip()
        video_url = request.POST.get("video_url", "").strip()
        is_breaking = bool(request.POST.get("is_breaking"))
        is_featured = bool(request.POST.get("is_featured"))

        if not title:   errors["title"]   = "Title is required."
        if not summary: errors["summary"] = "Summary is required."
        if not content: errors["content"] = "Content is required."

        if not errors:
            category = Category.objects.filter(pk=cat_id).first() if cat_id else None
            article = Article.objects.create(
                title=title, summary=summary, content=content,
                image_url=image_url, video_url=video_url, category=category,
                author=request.user, status=Article.Status.DRAFT,
                is_breaking=is_breaking if request.user.is_admin() else False,
                is_featured=is_featured if request.user.is_admin() else False,
            )
            ReviewNote.objects.create(article=article, actor=request.user, action=ReviewNote.Action.SUBMITTED,
                                      note="Article created as draft.")
            messages.success(request, f"Article '{article.title}' saved as draft.")
            return redirect("core:article_edit", slug=article.slug)

    return render(request, "core/article_form.html", {
        "categories": categories,
        "errors": errors,
        "form_data": form_data,
        "editing": False,
    })


@writer_required
def article_edit(request, slug):
    article    = get_object_or_404(Article, slug=slug)
    categories = Category.objects.all()

    if not article.can_edit(request.user):
        messages.error(request, "You cannot edit this article in its current state.")
        return redirect("core:editorial_dashboard")

    errors = {}

    if request.method == "POST":
        title     = request.POST.get("title", "").strip()
        summary   = request.POST.get("summary", "").strip()
        content   = request.POST.get("content", "").strip()
        cat_id    = request.POST.get("category", "").strip()
        image_url = request.POST.get("image_url", "").strip()
        video_url = request.POST.get("video_url", "").strip()
        is_breaking = bool(request.POST.get("is_breaking"))
        is_featured = bool(request.POST.get("is_featured"))

        if not title:   errors["title"]   = "Title is required."
        if not summary: errors["summary"] = "Summary is required."
        if not content: errors["content"] = "Content is required."

        if not errors:
            article.title     = title
            article.summary   = summary
            article.content   = content
            article.image_url = image_url
            article.video_url = video_url
            article.category  = Category.objects.filter(pk=cat_id).first() if cat_id else None
            if request.user.is_admin():
                article.is_breaking = is_breaking
                article.is_featured = is_featured
            article.save()

            # "Save & Submit" button
            if request.POST.get("save_and_submit") and article.can_submit(request.user):
                article.status       = Article.Status.SUBMITTED
                article.submitted_at = timezone.now()
                article.save(update_fields=["status", "submitted_at"])
                ReviewNote.objects.create(
                    article=article, actor=request.user,
                    action=ReviewNote.Action.SUBMITTED, note="",
                )
                messages.success(request, f"'{article.title}' saved and submitted for review.")
                return redirect("core:editorial_dashboard")

            messages.success(request, "Article saved.")
            return redirect("core:article_edit", slug=article.slug)

    return render(request, "core/article_form.html", {
        "article": article,
        "categories": categories,
        "errors": errors,
        "form_data": request.POST if request.method == "POST" else {},
        "editing": True,
    })


@writer_required
def article_submit(request, slug):
    if request.method != "POST":
        return redirect("core:editorial_dashboard")

    article = get_object_or_404(Article, slug=slug)
    if not article.can_submit(request.user):
        messages.error(request, "This article cannot be submitted in its current state.")
        return redirect("core:editorial_dashboard")

    article.status       = Article.Status.SUBMITTED
    article.submitted_at = timezone.now()
    article.save(update_fields=["status", "submitted_at"])

    ReviewNote.objects.create(
        article=article, actor=request.user,
        action=ReviewNote.Action.SUBMITTED,
        note=request.POST.get("note", ""),
    )
    messages.success(request, f"'{article.title}' has been submitted for review.")
    return redirect("core:editorial_dashboard")


@writer_required
def article_withdraw(request, slug):
    if request.method != "POST":
        return redirect("core:editorial_dashboard")

    article = get_object_or_404(Article, slug=slug)
    if not article.can_withdraw(request.user):
        messages.error(request, "This article cannot be withdrawn.")
        return redirect("core:editorial_dashboard")

    article.status = Article.Status.DRAFT
    article.save(update_fields=["status"])

    ReviewNote.objects.create(
        article=article, actor=request.user,
        action=ReviewNote.Action.WITHDRAWN,
        note="Withdrawn by author.",
    )
    messages.success(request, f"'{article.title}' has been withdrawn back to drafts.")
    return redirect("core:editorial_dashboard")


@writer_required
def article_delete(request, slug):
    if request.method != "POST":
        return redirect("core:editorial_dashboard")

    article = get_object_or_404(Article, slug=slug)
    if article.status != Article.Status.DRAFT or (not request.user.is_admin() and article.author != request.user):
        messages.error(request, "Only draft articles owned by you can be deleted.")
        return redirect("core:editorial_dashboard")

    title = article.title
    article.delete()
    messages.success(request, f"Article '{title}' deleted.")
    return redirect("core:editorial_dashboard")


@require_POST
def react_to_article(request, slug):
    if not request.user.is_authenticated:
        return JsonResponse({"error": "Login required"}, status=401)

    article = get_object_or_404(Article, slug=slug, status=Article.Status.PUBLISHED)
    reaction_type = request.POST.get("reaction", "")

    if reaction_type not in Reaction.Type.values:
        return JsonResponse({"error": "Invalid reaction"}, status=400)

    existing = Reaction.objects.filter(article=article, user=request.user).first()
    if existing:
        if existing.reaction_type == reaction_type:
            existing.delete()
            user_reaction = None
        else:
            existing.reaction_type = reaction_type
            existing.save(update_fields=["reaction_type"])
            user_reaction = reaction_type
    else:
        Reaction.objects.create(article=article, user=request.user, reaction_type=reaction_type)
        user_reaction = reaction_type

    counts = {r.value: 0 for r in Reaction.Type}
    for r in article.reactions.values("reaction_type").annotate(n=models.Count("id")):
        counts[r["reaction_type"]] = r["n"]

    return JsonResponse({"counts": counts, "user_reaction": user_reaction})


@writer_required
def article_preview(request, slug):
    article = get_object_or_404(Article, slug=slug)
    if not (request.user == article.author or request.user.is_admin()):
        messages.error(request, "You can only preview your own articles.")
        return redirect("core:editorial_dashboard")
    return render(request, "core/article_preview.html", {"article": article})


# ─────────────────────────────────────────────
# Review views  (reviewers + admins)
# ─────────────────────────────────────────────

@reviewer_required
def review_queue(request):
    status_filter = request.GET.get("status", "")
    qs = (
        Article.objects
        .filter(status__in=[Article.Status.SUBMITTED, Article.Status.IN_REVIEW])
        .select_related("category", "author", "reviewed_by")
        .order_by("submitted_at")
    )
    if status_filter in (Article.Status.SUBMITTED, Article.Status.IN_REVIEW):
        qs = qs.filter(status=status_filter)

    pending_count   = Article.objects.filter(status=Article.Status.SUBMITTED).count()
    in_review_count = Article.objects.filter(status=Article.Status.IN_REVIEW).count()

    return render(request, "core/review_queue.html", {
        "articles": qs,
        "pending_count": pending_count,
        "in_review_count": in_review_count,
        "status_filter": status_filter,
    })


@reviewer_required
def review_article(request, slug):
    article = get_object_or_404(
        Article.objects.select_related("category", "author", "reviewed_by"),
        slug=slug,
    )

    if article.status not in (Article.Status.SUBMITTED, Article.Status.IN_REVIEW, Article.Status.PUBLISHED):
        messages.error(request, "This article is not available for review.")
        return redirect("core:review_queue")

    # Auto-assign reviewer when they open a submitted article.
    if article.status == Article.Status.SUBMITTED:
        article.status      = Article.Status.IN_REVIEW
        article.reviewed_by = request.user
        article.save(update_fields=["status", "reviewed_by"])
        ReviewNote.objects.create(
            article=article, actor=request.user,
            action=ReviewNote.Action.IN_REVIEW,
            note=f"Taken for review by {request.user.email}.",
        )

    notes = article.review_notes.select_related("actor").all()

    return render(request, "core/review_article.html", {
        "article": article,
        "notes": notes,
    })


@reviewer_required
def review_action(request, slug):
    if request.method != "POST":
        return redirect("core:review_article", slug=slug)

    article = get_object_or_404(Article, slug=slug)
    action  = request.POST.get("action", "")
    note    = request.POST.get("note", "").strip()

    if article.status not in (Article.Status.IN_REVIEW, Article.Status.SUBMITTED):
        messages.error(request, "This article is not in a reviewable state.")
        return redirect("core:review_queue")

    if action == "approve":
        article.status      = Article.Status.PUBLISHED
        article.reviewed_at = timezone.now()
        article.reviewed_by = request.user
        article.published_at = timezone.now()
        article.save(update_fields=["status", "reviewed_at", "reviewed_by", "published_at"])
        ReviewNote.objects.create(
            article=article, actor=request.user,
            action=ReviewNote.Action.APPROVED, note=note,
        )
        messages.success(request, f"'{article.title}' approved and published.")
        return redirect("core:review_queue")

    elif action == "reject":
        if not note:
            messages.error(request, "A reason is required when rejecting an article.")
            return redirect("core:review_article", slug=slug)
        article.status      = Article.Status.REJECTED
        article.reviewed_at = timezone.now()
        article.reviewed_by = request.user
        article.save(update_fields=["status", "reviewed_at", "reviewed_by"])
        ReviewNote.objects.create(
            article=article, actor=request.user,
            action=ReviewNote.Action.REJECTED, note=note,
        )
        messages.success(request, f"'{article.title}' rejected with feedback.")
        return redirect("core:review_queue")

    elif action == "comment":
        if note:
            ReviewNote.objects.create(
                article=article, actor=request.user,
                action=ReviewNote.Action.COMMENT, note=note,
            )
            messages.success(request, "Comment added.")
        return redirect("core:review_article", slug=slug)

    messages.error(request, "Unknown action.")
    return redirect("core:review_article", slug=slug)


# ─────────────────────────────────────────────
# Telegram import views  (admins only)
# ─────────────────────────────────────────────

@admin_required
@require_POST
def fetch_telegram(request):
    from .services import fetch_telegram_messages, fetch_all_channels, get_active_channels

    channel = request.POST.get("channel", "").strip()
    active  = get_active_channels()

    if channel:
        if channel not in active:
            messages.error(request, f"Unknown channel '{channel}'.")
            return redirect("core:telegram_imports")
        try:
            batch = fetch_telegram_messages(channel, count=5)
        except Exception as exc:
            messages.error(request, f"Could not reach @{channel}: {exc}")
            return redirect("core:telegram_imports")
        all_fetched = batch
        # Update last_fetched_at
        TelegramChannel.objects.filter(slug=channel).update(last_fetched_at=timezone.now())
    else:
        results = fetch_all_channels(count_per_channel=5)
        all_fetched = []
        for ch, outcome in results.items():
            if isinstance(outcome, Exception):
                messages.warning(request, f"@{ch}: {outcome}")
            else:
                all_fetched.extend(outcome)
                TelegramChannel.objects.filter(slug=ch).update(last_fetched_at=timezone.now())

    created = 0
    for item in all_fetched:
        _, was_created = TelegramImport.objects.get_or_create(
            message_id=item["message_id"],
            defaults={
                "channel":    item.get("channel", ""),
                "source_url": item["source_url"],
                "raw_text":   item["raw_text"],
                "date":       item["date"],
                "image_urls": item.get("image_urls", []),
            },
        )
        if was_created:
            created += 1

    if created:
        messages.success(request, f"Fetched {created} new message{'s' if created != 1 else ''}.")
    else:
        messages.info(request, "No new messages — everything is already imported.")
    return redirect("core:telegram_imports")


@admin_required
def telegram_import_list(request):
    status_filter  = request.GET.get("status", "pending")
    channel_filter = request.GET.get("channel", "")
    if status_filter not in TelegramImport.Status.values:
        status_filter = "pending"

    active_channels = TelegramChannel.objects.filter(is_active=True)
    active_slugs    = [ch.slug for ch in active_channels]

    qs = TelegramImport.objects.filter(status=status_filter)
    if channel_filter and channel_filter in active_slugs:
        qs = qs.filter(channel=channel_filter)

    counts = {s.value: TelegramImport.objects.filter(status=s).count() for s in TelegramImport.Status}

    return render(request, "core/telegram_imports.html", {
        "imports":        qs,
        "counts":         counts,
        "status_filter":  status_filter,
        "channel_filter": channel_filter,
        "statuses":       TelegramImport.Status,
        "channels":       active_channels,
    })


@admin_required
def approve_import(request, pk):
    item = get_object_or_404(TelegramImport, pk=pk, status=TelegramImport.Status.PENDING)
    categories = Category.objects.all()

    if request.method == "POST":
        title      = request.POST.get("title", "").strip()
        summary    = request.POST.get("summary", "").strip()
        content     = request.POST.get("content", "").strip()
        category_id = request.POST.get("category") or None
        image_url   = request.POST.get("image_url", "").strip()
        is_featured = request.POST.get("is_featured") == "on"
        is_breaking = request.POST.get("is_breaking") == "on"

        if not title:
            messages.error(request, "Title is required.")
        elif not content:
            messages.error(request, "Content is required.")
        elif not summary:
            messages.error(request, "Summary is required.")
        else:
            article = Article.objects.create(
                title=title,
                summary=summary,
                content=content,
                image_url=image_url,
                category_id=category_id,
                author=request.user,
                status=Article.Status.PUBLISHED,
                published_at=timezone.now(),
                is_featured=is_featured,
                is_breaking=is_breaking,
            )
            item.article = article
            item.status  = TelegramImport.Status.APPROVED
            item.save()
            messages.success(request, f"Article \"{title}\" published.")
            return redirect("core:telegram_imports")

    channel_obj = TelegramChannel.objects.filter(slug=item.channel).first()

    return render(request, "core/approve_import.html", {
        "item":        item,
        "categories":  categories,
        "channel_obj": channel_obj,
    })


@admin_required
@require_POST
def reject_import(request, pk):
    item = get_object_or_404(TelegramImport, pk=pk, status=TelegramImport.Status.PENDING)
    item.status = TelegramImport.Status.REJECTED
    item.save()
    messages.success(request, "Import rejected.")
    return redirect("core:telegram_imports")


# ─────────────────────────────────────────────
# Channel management views  (admins only)
# ─────────────────────────────────────────────

@admin_required
def channel_list(request):
    channels = TelegramChannel.objects.all()
    return render(request, "core/channel_list.html", {"channels": channels})


@admin_required
def channel_create(request):
    if request.method == "POST":
        slug         = request.POST.get("slug", "").strip().lower()
        display_name = request.POST.get("display_name", "").strip()
        interval     = request.POST.get("fetch_interval", "5").strip()

        errors = {}
        if not slug:
            errors["slug"] = "Username is required."
        elif TelegramChannel.objects.filter(slug=slug).exists():
            errors["slug"] = "A channel with this username already exists."
        if not display_name:
            errors["display_name"] = "Display name is required."
        try:
            interval = max(1, int(interval))
        except ValueError:
            interval = 5

        if not errors:
            TelegramChannel.objects.create(
                slug=slug,
                display_name=display_name,
                fetch_interval=interval,
                is_active=True,
            )
            messages.success(request, f"Channel @{slug} added.")
            return redirect("core:channel_list")

        return render(request, "core/channel_form.html", {
            "errors": errors,
            "form_data": request.POST,
        })

    return render(request, "core/channel_form.html", {"errors": {}, "form_data": {}})


@admin_required
@require_POST
def channel_toggle(request, pk):
    channel = get_object_or_404(TelegramChannel, pk=pk)
    channel.is_active = not channel.is_active
    channel.save(update_fields=["is_active"])
    state = "activated" if channel.is_active else "deactivated"
    messages.success(request, f"@{channel.slug} {state}.")
    return redirect("core:channel_list")


@admin_required
@require_POST
def channel_delete(request, pk):
    channel = get_object_or_404(TelegramChannel, pk=pk)
    slug = channel.slug
    channel.delete()
    messages.success(request, f"Channel @{slug} deleted.")
    return redirect("core:channel_list")
