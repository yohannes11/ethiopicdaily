from django.contrib import messages
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from ..decorators import reviewer_required
from ..models import Article, ReviewNote


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

    pending_count = Article.objects.filter(status=Article.Status.SUBMITTED).count()
    in_review_count = Article.objects.filter(status=Article.Status.IN_REVIEW).count()

    paginator = Paginator(qs, 20)
    page_obj = paginator.get_page(request.GET.get("page"))

    return render(request, "core/review_queue.html", {
        "articles": page_obj,
        "page_obj": page_obj,
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

    if article.status not in (
        Article.Status.SUBMITTED, Article.Status.IN_REVIEW, Article.Status.PUBLISHED
    ):
        messages.error(request, "This article is not available for review.")
        return redirect("core:review_queue")

    if article.status == Article.Status.SUBMITTED:
        Article.objects.filter(pk=article.pk).update(
            status=Article.Status.IN_REVIEW,
            reviewed_by=request.user,
        )
        article.refresh_from_db()
        ReviewNote.objects.create(
            article=article, actor=request.user,
            action=ReviewNote.Action.IN_REVIEW,
            note=f"Taken for review by {request.user.email}.",
        )

    notes = article.review_notes.select_related("actor").order_by("created_at")

    return render(request, "core/review_article.html", {
        "article": article,
        "notes": notes,
    })


@reviewer_required
def review_action(request, slug):
    if request.method != "POST":
        return redirect("core:review_article", slug=slug)

    article = get_object_or_404(Article, slug=slug)
    action = request.POST.get("action", "")
    note = request.POST.get("note", "").strip()

    if article.status not in (Article.Status.IN_REVIEW, Article.Status.SUBMITTED):
        messages.error(request, "This article is not in a reviewable state.")
        return redirect("core:review_queue")

    if action == "approve":
        now = timezone.now()
        article.status = Article.Status.PUBLISHED
        article.reviewed_at = now
        article.reviewed_by = request.user
        article.published_at = now
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
        article.status = Article.Status.REJECTED
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
