from django.db import models as db_models
from django.db.models import Count, F, Q
from django.http import Http404, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from ..models import Article, Category, Reaction


def homepage(request):
    published = Article.objects.filter(
        status=Article.Status.PUBLISHED
    ).select_related("category", "author")

    featured = published.filter(is_featured=True).first()

    exclude_pk = featured.pk if featured else 0
    sub_hero = published.exclude(pk=exclude_pk).order_by("-published_at")[:3]

    latest = published.exclude(pk=exclude_pk).order_by("-published_at")[:8]

    trending = published.select_related("category").order_by("-views_count")[:6]
    most_read = published.select_related("category").order_by("-views_count")[:5]
    categories = Category.objects.all()

    category_sections = []
    for cat in categories[:4]:
        arts = list(
            published.filter(category=cat)
            .select_related("category", "author")
            .order_by("-published_at")[:4]
        )
        if arts:
            category_sections.append({"category": cat, "articles": arts})

    return render(request, "core/home.html", {
        "featured": featured,
        "sub_hero": sub_hero,
        "latest": latest,
        "trending": trending,
        "most_read": most_read,
        "category_sections": category_sections,
    })


def search(request):
    query = request.GET.get("q", "").strip()
    results = []
    if query:
        results = (
            Article.objects.filter(status=Article.Status.PUBLISHED)
            .filter(
                Q(title__icontains=query)
                | Q(summary__icontains=query)
                | Q(content__icontains=query)
            )
            .select_related("category", "author")
            .order_by("-published_at")
        )
    return render(request, "core/search_results.html", {
        "query": query,
        "results": results,
    })


def article_detail(request, slug):
    article = get_object_or_404(
        Article.objects.select_related("category", "author"), slug=slug
    )

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
        Article.objects.filter(pk=article.pk).update(views_count=F("views_count") + 1)

    related = (
        Article.objects
        .filter(category=article.category, status=Article.Status.PUBLISHED)
        .exclude(pk=article.pk)
        .select_related("category")
        .order_by("-published_at")[:3]
    )

    can_edit = request.user.is_authenticated and article.can_edit(request.user)

    reaction_counts = {r.value: 0 for r in Reaction.Type}
    for r in article.reactions.values("reaction_type").annotate(n=Count("id")):
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
        response.set_cookie(
            cookie_key, "1",
            max_age=30 * 24 * 60 * 60,
            httponly=True,
            samesite="Lax",
        )
    return response


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
    for r in article.reactions.values("reaction_type").annotate(n=Count("id")):
        counts[r["reaction_type"]] = r["n"]

    return JsonResponse({"counts": counts, "user_reaction": user_reaction})
