from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.db.models import Q
from django.shortcuts import redirect, render

from content.forms import QuickAddForm
from content.models import ContentItem, DiscoveryPreference
from content.providers import NETWORK_PROVIDERS
from content.services import (
    fetch_free_archive_movies,
    fetch_live_tv_schedule,
    fetch_trending_movies,
    fetch_trending_tv,
)
from watchlist.models import Watchlist

DISCOVERY_GENRES = (
    'Action', 'Adventure', 'Animation', 'Comedy', 'Crime', 'Documentary', 'Drama',
    'Family', 'Fantasy', 'History', 'Horror', 'Kids', 'Music', 'Mystery', 'News',
    'Reality', 'Romance', 'Sci-Fi & Fantasy', 'Science Fiction', 'Soap', 'Sports',
    'Talk', 'Thriller', 'War & Politics', 'Western',
)


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


@login_required
def profile(request):
    preference, _ = DiscoveryPreference.objects.get_or_create(user=request.user)
    if request.method == 'POST':
        selected = [
            genre for genre in request.POST.getlist('preferred_genres')
            if genre in DISCOVERY_GENRES
        ]
        preference.preferred_genres = selected
        preference.customized = True
        preference.save(update_fields=['preferred_genres', 'customized'])
        return redirect('profile')

    selected = preference.preferred_genres if preference.customized else list(DISCOVERY_GENRES)
    return render(request, 'accounts/profile.html', {
        'discovery_genres': DISCOVERY_GENRES,
        'preferred_genres': selected,
        'preferences_customized': preference.customized,
    })


def _filter_discovery(items, preferred_genres, customized=False):
    if not customized:
        return items
    wanted = {genre.casefold() for genre in preferred_genres}
    filtered = []
    for item in items:
        categories = {str(value).casefold() for value in item.get('genres', [])}
        show_type = str(item.get('show_type') or '').strip()
        if show_type:
            categories.add(show_type.casefold())
        if item.get('is_news'):
            categories.add('news')
        if categories & wanted:
            filtered.append(item)
    return filtered


def home(request):
    db_queryset = ContentItem.objects.prefetch_related('availabilities').all()

    preference = None
    if request.user.is_authenticated:
        preference, _ = DiscoveryPreference.objects.get_or_create(user=request.user)

    if request.method == 'POST' and request.user.is_authenticated:
        form = QuickAddForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('/')
    else:
        form = QuickAddForm()

    customized = bool(preference and preference.customized)
    preferred_genres = preference.preferred_genres if customized else list(DISCOVERY_GENRES)

    live_tv = _filter_discovery(fetch_live_tv_schedule(), preferred_genres, customized=customized)
    free_movies = fetch_free_archive_movies()
    trending_movies = _filter_discovery(fetch_trending_movies(), preferred_genres, customized=customized)
    trending_tv = _filter_discovery(fetch_trending_tv(), preferred_genres, customized=customized)

    watchlist_ids = []
    saved_external_ids = {}
    if request.user.is_authenticated:
        saved_items = list(Watchlist.objects.filter(user=request.user).select_related('content'))
        watchlist_ids = [entry.content_id for entry in saved_items]
        saved_external_ids = {
            (entry.content.external_source, entry.content.external_id, entry.content.content_type): entry.content_id
            for entry in saved_items
            if entry.content.external_source and entry.content.external_id
        }

    for item in [*live_tv, *free_movies, *trending_movies, *trending_tv]:
        item['saved_content_id'] = saved_external_ids.get(
            (item.get('external_source'), item.get('external_id'), item.get('content_type'))
        )

    db_items = list(db_queryset)
    network_items = [
        item for item in db_items
        if any(availability.provider in NETWORK_PROVIDERS for availability in item.availabilities.all())
    ]

    query = request.GET.get('q', '').strip()
    content_type = request.GET.get('type', '').strip()
    provider = request.GET.get('provider', '').strip()
    browse_active = bool(query or content_type or provider)
    browse_results = []
    if browse_active:
        browse_queryset = db_queryset
        if query:
            browse_queryset = browse_queryset.filter(
                Q(title__icontains=query) | Q(genre__icontains=query) | Q(description__icontains=query)
            )
        if content_type in {ContentItem.ContentType.MOVIE, ContentItem.ContentType.TV, ContentItem.ContentType.VIDEO}:
            browse_queryset = browse_queryset.filter(content_type=content_type)
        if provider:
            browse_queryset = browse_queryset.filter(availabilities__provider__iexact=provider)
        browse_results = list(browse_queryset.distinct().order_by('title'))

    providers = sorted({
        availability.provider
        for item in db_items
        for availability in item.availabilities.all()
        if availability.provider
    })

    context = {
        'form': form,
        'live_tv': live_tv,
        'free_movies': free_movies,
        'trending_movies': trending_movies[:10],
        'trending_tv': trending_tv[:10],
        'network_items': network_items,
        'movies': [x for x in db_items if x.content_type == ContentItem.ContentType.MOVIE],
        'tv': [x for x in db_items if x.content_type == ContentItem.ContentType.TV],
        'youtube': [x for x in db_items if x.source_type == 'youtube'],
        'watchlist_ids': watchlist_ids,
        'browse_active': browse_active,
        'browse_results': browse_results,
        'browse_query': query,
        'browse_type': content_type,
        'browse_provider': provider,
        'providers': providers,
        'preferences_customized': customized,
    }
    return render(request, 'home.html', context)
