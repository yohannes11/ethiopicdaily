from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from ..decorators import writer_required
from ..forms import ArticleForm, ArticleSearchForm
from ..models import Article, Category, ReviewNote, TelegramImport
from users.models import User


@writer_required
def editorial_dashboard(request):
    if request.user.is_admin():
        qs = Article.objects.select_related("category", "author").order_by("-updated_at")
    else:
        qs = Article.objects.filter(author=request.user).select_related("category").order_by("-updated_at")

    # Counts always reflect unfiltered totals for the stat cards
    base_qs = Article.objects if request.user.is_admin() else Article.objects.filter(author=request.user)
    counts = dict(
        base_qs.values_list("status").annotate(n=Count("id")).values_list("status", "n")
    )
    for s in Article.Status:
        counts.setdefault(s.value, 0)

    # Search form — bound when any GET params present
    search_form = ArticleSearchForm(request.GET or None, user=request.user)
    current_status = ""

    if search_form.is_valid():
        cd = search_form.cleaned_data
        q = cd.get("q", "").strip()
        status = cd.get("status", "")
        category = cd.get("category")
        author_email = cd.get("author_email", "").strip()
        date_from = cd.get("date_from")
        date_to = cd.get("date_to")
        is_featured = cd.get("is_featured", "")
        is_breaking = cd.get("is_breaking", "")

        if q:
            qs = qs.filter(Q(title__icontains=q) | Q(summary__icontains=q) | Q(content__icontains=q))
        if status and status in Article.Status.values:
            qs = qs.filter(status=status)
            current_status = status
        if category:
            qs = qs.filter(category=category)
        if author_email and request.user.is_admin():
            qs = qs.filter(author__email__icontains=author_email)
        if date_from:
            qs = qs.filter(created_at__date__gte=date_from)
        if date_to:
            qs = qs.filter(created_at__date__lte=date_to)
        if is_featured == "1":
            qs = qs.filter(is_featured=True)
        elif is_featured == "0":
            qs = qs.filter(is_featured=False)
        if is_breaking == "1":
            qs = qs.filter(is_breaking=True)
        elif is_breaking == "0":
            qs = qs.filter(is_breaking=False)

    paginator = Paginator(qs, 20)
    page_obj = paginator.get_page(request.GET.get("page"))

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
        "articles": page_obj,
        "page_obj": page_obj,
        "search_form": search_form,
        "status_choices": Article.Status.choices,
        "current_status": current_status,
        "counts": counts,
        **extra,
    })


@writer_required
def article_create(request):
    if request.method == "POST":
        form = ArticleForm(request.POST, user=request.user)
        if form.is_valid():
            article = form.save(commit=False)
            article.author = request.user
            article.status = Article.Status.DRAFT
            if not request.user.is_admin():
                article.is_featured = False
                article.is_breaking = False
            article.save()
            ReviewNote.objects.create(
                article=article, actor=request.user,
                action=ReviewNote.Action.COMMENT,
                note="Article created as draft.",
            )
            messages.success(request, f"Article '{article.title}' saved as draft.")
            return redirect("core:article_edit", slug=article.slug)

        return render(request, "core/article_form.html", {
            "form": form,
            "categories": Category.objects.all(),
            "editing": False,
        })

    return render(request, "core/article_form.html", {
        "form": ArticleForm(user=request.user),
        "categories": Category.objects.all(),
        "editing": False,
    })


@writer_required
def article_edit(request, slug):
    article = get_object_or_404(Article, slug=slug)

    if not article.can_edit(request.user):
        messages.error(request, "You cannot edit this article in its current state.")
        return redirect("core:editorial_dashboard")

    if request.method == "POST":
        form = ArticleForm(request.POST, instance=article, user=request.user)
        if form.is_valid():
            updated = form.save(commit=False)
            if not request.user.is_admin():
                updated.is_featured = article.is_featured
                updated.is_breaking = article.is_breaking
            updated.save()

            if request.POST.get("save_and_submit") and updated.can_submit(request.user):
                updated.status = Article.Status.SUBMITTED
                updated.submitted_at = timezone.now()
                updated.save(update_fields=["status", "submitted_at"])
                ReviewNote.objects.create(
                    article=updated, actor=request.user,
                    action=ReviewNote.Action.SUBMITTED, note="",
                )
                messages.success(request, f"'{updated.title}' saved and submitted for review.")
                return redirect("core:editorial_dashboard")

            messages.success(request, "Article saved.")
            return redirect("core:article_edit", slug=updated.slug)

        return render(request, "core/article_form.html", {
            "form": form,
            "article": article,
            "categories": Category.objects.all(),
            "editing": True,
        })

    return render(request, "core/article_form.html", {
        "form": ArticleForm(instance=article, user=request.user),
        "article": article,
        "categories": Category.objects.all(),
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

    article.status = Article.Status.SUBMITTED
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
    if article.status != Article.Status.DRAFT or (
        not request.user.is_admin() and article.author != request.user
    ):
        messages.error(request, "Only draft articles owned by you can be deleted.")
        return redirect("core:editorial_dashboard")

    title = article.title
    article.delete()
    messages.success(request, f"Article '{title}' deleted.")
    return redirect("core:editorial_dashboard")


@writer_required
def article_preview(request, slug):
    article = get_object_or_404(Article, slug=slug)
    if not (request.user == article.author or request.user.is_admin()):
        messages.error(request, "You can only preview your own articles.")
        return redirect("core:editorial_dashboard")
    return render(request, "core/article_preview.html", {"article": article})
