from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from content.models import ContentItem
from .models import Watchlist


def _watchlist_response(request, *, content, saved):
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({
            'saved': saved,
            'content_id': content.id,
            'label': '✓ Saved to Watchlist' if saved else '⭐ Save to Watchlist',
        })
    return redirect('/')


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
    return _watchlist_response(request, content=content, saved=True)


@login_required
@require_POST
def remove_from_watchlist(request, content_id):
    content = get_object_or_404(ContentItem, id=content_id)
    Watchlist.objects.filter(user=request.user, content=content).delete()
    return _watchlist_response(request, content=content, saved=False)
