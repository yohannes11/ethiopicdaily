from django.contrib import messages
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from ..decorators import admin_required
from ..forms import ChannelForm
from ..models import Article, Category, TelegramChannel, TelegramImport


@admin_required
@require_POST
def fetch_telegram(request):
    from ..services import fetch_telegram_messages, fetch_all_channels, get_active_channels

    channel = request.POST.get("channel", "").strip()
    active = get_active_channels()

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
    status_filter = request.GET.get("status", "pending")
    channel_filter = request.GET.get("channel", "")
    if status_filter not in TelegramImport.Status.values:
        status_filter = "pending"

    active_channels = TelegramChannel.objects.filter(is_active=True)
    active_slugs = [ch.slug for ch in active_channels]

    qs = TelegramImport.objects.filter(status=status_filter)
    if channel_filter and channel_filter in active_slugs:
        qs = qs.filter(channel=channel_filter)

    counts = {s.value: TelegramImport.objects.filter(status=s).count() for s in TelegramImport.Status}

    paginator = Paginator(qs, 25)
    page_obj = paginator.get_page(request.GET.get("page"))

    return render(request, "core/telegram_imports.html", {
        "imports": page_obj,
        "page_obj": page_obj,
        "counts": counts,
        "status_filter": status_filter,
        "channel_filter": channel_filter,
        "statuses": TelegramImport.Status,
        "channels": active_channels,
    })


@admin_required
def approve_import(request, pk):
    item = get_object_or_404(TelegramImport, pk=pk, status=TelegramImport.Status.PENDING)
    categories = Category.objects.all()

    if request.method == "POST":
        title = request.POST.get("title", "").strip()
        summary = request.POST.get("summary", "").strip()
        content = request.POST.get("content", "").strip()
        category_id = request.POST.get("category") or None
        image_url = request.POST.get("image_url", "").strip()
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
            item.status = TelegramImport.Status.APPROVED
            item.save()
            messages.success(request, f'Article "{title}" published.')
            return redirect("core:telegram_imports")

    channel_obj = TelegramChannel.objects.filter(slug=item.channel).first()

    return render(request, "core/approve_import.html", {
        "item": item,
        "categories": categories,
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


@admin_required
def channel_list(request):
    channels = TelegramChannel.objects.all()
    return render(request, "core/channel_list.html", {"channels": channels})


@admin_required
def channel_create(request):
    if request.method == "POST":
        form = ChannelForm(request.POST)
        if form.is_valid():
            channel = form.save(commit=False)
            channel.is_active = True
            channel.save()
            messages.success(request, f"Channel @{channel.slug} added.")
            return redirect("core:channel_list")
        errors = {field: error_list[0] for field, error_list in form.errors.items()}
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
