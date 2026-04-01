from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render

from ..decorators import admin_required
from ..forms import AdvertisementForm
from ..models import Advertisement


@admin_required
def ad_list(request):
    ads = Advertisement.objects.all()
    # Group by placement for display
    by_placement = {}
    for placement, label in Advertisement.Placement.choices:
        by_placement[placement] = {
            "label": label,
            "ads": [a for a in ads if a.placement == placement],
        }
    return render(request, "core/ad_list.html", {
        "by_placement": by_placement,
        "total": ads.count(),
        "active_count": ads.filter(is_active=True).count(),
    })


@admin_required
def ad_create(request):
    if request.method == "POST":
        form = AdvertisementForm(request.POST)
        if form.is_valid():
            ad = form.save()
            messages.success(request, f"Ad '{ad.name}' created and {'active' if ad.is_active else 'paused'}.")
            return redirect("core:ad_list")
    else:
        form = AdvertisementForm()

    return render(request, "core/ad_form.html", {"form": form, "editing": False})


@admin_required
def ad_edit(request, pk):
    ad = get_object_or_404(Advertisement, pk=pk)

    if request.method == "POST":
        form = AdvertisementForm(request.POST, instance=ad)
        if form.is_valid():
            updated = form.save()
            messages.success(request, f"Ad '{updated.name}' updated.")
            return redirect("core:ad_list")
    else:
        form = AdvertisementForm(instance=ad)

    return render(request, "core/ad_form.html", {"form": form, "ad": ad, "editing": True})


@admin_required
def ad_toggle(request, pk):
    if request.method != "POST":
        return redirect("core:ad_list")
    ad = get_object_or_404(Advertisement, pk=pk)
    ad.is_active = not ad.is_active
    ad.save(update_fields=["is_active"])
    state = "activated" if ad.is_active else "paused"
    messages.success(request, f"Ad '{ad.name}' {state}.")
    return redirect("core:ad_list")


@admin_required
def ad_delete(request, pk):
    if request.method != "POST":
        return redirect("core:ad_list")
    ad = get_object_or_404(Advertisement, pk=pk)
    name = ad.name
    ad.delete()
    messages.success(request, f"Ad '{name}' deleted.")
    return redirect("core:ad_list")