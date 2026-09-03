from django.contrib.auth import login
from django.contrib.auth.forms import UserCreationForm
from django.shortcuts import redirect, render

from content.forms import QuickAddForm
from content.models import ContentItem
from content.providers import NETWORK_PROVIDERS
from content.services import fetch_trending_movies, fetch_trending_tv
from watchlist.models import Watchlist


def register(request):
    if request.user.is_authenticated:
        return redirect('home')

    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('home')
    else:
        form = UserCreationForm()

    return render(request, 'registration/register.html', {'form': form})


def _mark_saved_discovery_items(items, saved_external_items):
    for item in items:
        key = (
            item.get('external_source', ''),
            item.get('external_id', ''),
            item.get('content_type', ''),
        )
        item['saved_content_id'] = saved_external_items.get(key)


def home(request):
    db_items = list(ContentItem.objects.prefetch_related('availabilities').all())

    if request.method == 'POST' and request.user.is_authenticated:
        form = QuickAddForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('/')
    else:
        form = QuickAddForm()

    trending_movies = fetch_trending_movies()
    trending_tv = fetch_trending_tv()

    watchlist_ids = []
    saved_external_items = {}
    if request.user.is_authenticated:
        watchlist_entries = list(
            Watchlist.objects.filter(user=request.user)
            .select_related('content')
        )
        watchlist_ids = [entry.content_id for entry in watchlist_entries]
        saved_external_items = {
            (
                entry.content.external_source,
                entry.content.external_id,
                entry.content.content_type,
            ): entry.content_id
            for entry in watchlist_entries
            if entry.content.external_source and entry.content.external_id
        }

    _mark_saved_discovery_items(trending_movies, saved_external_items)
    _mark_saved_discovery_items(trending_tv, saved_external_items)

    network_items = [
        item
        for item in db_items
        if any(
            availability.provider in NETWORK_PROVIDERS
            for availability in item.availabilities.all()
        )
    ]

    context = {
        'form': form,
        'trending_movies': trending_movies[:10],
        'trending_tv': trending_tv[:10],
        'network_items': network_items,
        'movies': [x for x in db_items if x.content_type == ContentItem.ContentType.MOVIE],
        'tv': [x for x in db_items if x.content_type == ContentItem.ContentType.TV],
        'youtube': [x for x in db_items if x.source_type == 'youtube'],
        'watchlist_ids': watchlist_ids,
    }

    return render(request, 'home.html', context)
