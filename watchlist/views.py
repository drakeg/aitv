from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_POST

from content.models import ContentItem
from .models import Watchlist


def _safe_fallback_url(request):
    candidate = request.POST.get('next') or request.META.get('HTTP_REFERER')
    if candidate and url_has_allowed_host_and_scheme(
        candidate,
        allowed_hosts={request.get_host()},
        require_https=request.is_secure(),
    ):
        return candidate
    return '/'


def _watchlist_response(request, *, content, saved):
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({
            'saved': saved,
            'content_id': content.id,
            'label': '✓ Saved to Watchlist' if saved else '⭐ Save to Watchlist',
            'add_url': reverse('watchlist:add', args=[content.id]),
            'remove_url': reverse('watchlist:remove', args=[content.id]),
        })
    return redirect(_safe_fallback_url(request))


def _clear_release_baseline(user, content_id):
    from notifications.models import ReleaseWatchState

    ReleaseWatchState.objects.filter(user=user, content_id=content_id).delete()


@login_required
def watchlist(request):
    entries = list(
        Watchlist.objects.filter(user=request.user)
        .select_related('content')
        .prefetch_related('content__availabilities')
        .order_by('-is_favorite', '-added_at')
    )
    watchlist_ids = [entry.content_id for entry in entries]
    return render(
        request,
        'watchlist/list.html',
        {
            'entries': entries,
            'watchlist_ids': watchlist_ids,
            'favorite_count': sum(1 for entry in entries if entry.is_favorite),
        },
    )


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
    deleted, _ = Watchlist.objects.filter(user=request.user, content=content).delete()
    if deleted:
        _clear_release_baseline(request.user, content_id)
    return _watchlist_response(request, content=content, saved=False)


@login_required
@require_POST
def set_favorite(request, content_id):
    entry = get_object_or_404(Watchlist, user=request.user, content_id=content_id)
    favorite = request.POST.get('favorite') == '1'
    if entry.is_favorite != favorite:
        entry.is_favorite = favorite
        entry.save(update_fields=['is_favorite'])
        _clear_release_baseline(request.user, content_id)
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({
            'content_id': content_id,
            'favorite': entry.is_favorite,
            'label': '★ Favorite' if entry.is_favorite else '☆ Mark favorite',
        })
    return redirect(_safe_fallback_url(request))
