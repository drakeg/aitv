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
    if request.user.is_authenticated:
        watchlist_ids = list(
            Watchlist.objects.filter(user=request.user)
            .values_list('content_id', flat=True)
        )

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
