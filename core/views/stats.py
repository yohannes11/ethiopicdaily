from datetime import timedelta

from django.db.models import Count
from django.shortcuts import render
from django.utils import timezone

from users.models import User

from ..decorators import admin_required
from ..models import Article, PageView


@admin_required
def stats_dashboard(request):
    today      = timezone.localdate()
    yesterday  = today - timedelta(days=1)
    week_ago   = today - timedelta(days=6)
    month_ago  = today - timedelta(days=29)

    # ── Headline numbers ──────────────────────────────────────────
    views_today     = PageView.objects.filter(date=today).count()
    views_yesterday = PageView.objects.filter(date=yesterday).count()
    views_7d        = PageView.objects.filter(date__gte=week_ago).count()
    views_30d       = PageView.objects.filter(date__gte=month_ago).count()

    unique_today = (
        PageView.objects
        .filter(date=today)
        .exclude(session_key='')
        .values('session_key')
        .distinct()
        .count()
    )

    # ── 14-day bar chart ─────────────────────────────────────────
    two_weeks_ago = today - timedelta(days=13)
    daily_qs = (
        PageView.objects
        .filter(date__gte=two_weeks_ago)
        .values('date')
        .annotate(count=Count('id'))
    )
    daily_map = {row['date']: row['count'] for row in daily_qs}
    chart_data = [
        {'date': (two_weeks_ago + timedelta(days=i)).strftime('%b %d'),
         'count': daily_map.get(two_weeks_ago + timedelta(days=i), 0)}
        for i in range(14)
    ]
    chart_max = max((d['count'] for d in chart_data), default=1) or 1

    # ── Top pages ────────────────────────────────────────────────
    top_pages = (
        PageView.objects
        .filter(date__gte=month_ago)
        .values('path')
        .annotate(count=Count('id'))
        .order_by('-count')[:10]
    )

    # ── Top articles (all-time by views_count) ───────────────────
    top_articles = (
        Article.objects
        .filter(status=Article.Status.PUBLISHED)
        .order_by('-views_count')
        .select_related('author', 'category')[:10]
    )

    # ── Article status breakdown ─────────────────────────────────
    status_raw = dict(
        Article.objects.values('status').annotate(c=Count('id')).values_list('status', 'c')
    )
    total_articles = sum(status_raw.values()) or 1
    status_counts = [
        {'label': label, 'value': value,
         'count': status_raw.get(value, 0),
         'pct': round(status_raw.get(value, 0) / total_articles * 100)}
        for value, label in Article.Status.choices
    ]

    # ── User activity ────────────────────────────────────────────
    user_activity = (
        User.objects
        .filter(articles__isnull=False)
        .annotate(article_count=Count('articles'))
        .order_by('-article_count')[:8]
    )

    return render(request, 'core/stats_dashboard.html', {
        'views_today':     views_today,
        'views_yesterday': views_yesterday,
        'views_7d':        views_7d,
        'views_30d':       views_30d,
        'unique_today':    unique_today,
        'chart_data':      chart_data,
        'chart_max':       chart_max,
        'top_pages':       top_pages,
        'top_articles':    top_articles,
        'status_counts':   status_counts,
        'user_activity':   user_activity,
        'today':           today,
    })
