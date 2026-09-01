from django.shortcuts import redirect
from django.contrib.auth.decorators import login_required
from .models import Watchlist
from content.models import ContentItem

@login_required
def add_to_watchlist(request, content_id):
    content = ContentItem.objects.get(id=content_id)
    Watchlist.objects.get_or_create(user=request.user, content=content)
    return redirect(request.META.get('HTTP_REFERER', '/'))

@login_required
def remove_from_watchlist(request, content_id):
    content = ContentItem.objects.get(id=content_id)
    Watchlist.objects.filter(user=request.user, content=content).delete()
    return redirect(request.META.get('HTTP_REFERER', '/'))
