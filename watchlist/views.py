from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from content.models import ContentItem
from .models import Watchlist


@login_required
def watchlist(request):
    entries = (
        Watchlist.objects.filter(user=request.user)
        .select_related('content')
        .prefetch_related('content__availabilities')
        .order_by('-added_at')
    )
    return render(request, 'watchlist/list.html', {'entries': entries})


@login_required
@require_POST
def add_to_watchlist(request, content_id):
    content = get_object_or_404(ContentItem, id=content_id)
    Watchlist.objects.get_or_create(user=request.user, content=content)
    return redirect(request.POST.get('next') or request.META.get('HTTP_REFERER', '/'))


@login_required
@require_POST
def remove_from_watchlist(request, content_id):
    content = get_object_or_404(ContentItem, id=content_id)
    Watchlist.objects.filter(user=request.user, content=content).delete()
    return redirect(request.POST.get('next') or request.META.get('HTTP_REFERER', '/'))
