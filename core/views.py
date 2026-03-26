from django.shortcuts import render


def under_construction(request):
    return render(request, 'core/under_construction.html')
