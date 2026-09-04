from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.shortcuts import redirect, render

from content.models import DiscoveryPreference
from content.services import (
    fetch_free_archive_movies,
    fetch_live_tv_schedule,
    fetch_popular_tv,
    fetch_trending_movies,
    fetch_trending_tv,
    fetch_tv_on_the_air,
)
from watchlist.models import Watchlist

from .forms import AccountProfileForm

DISCOVERY_GENRES = (
    'Action', 'Adventure', 'Animation', 'Comedy', 'Crime', 'Documentary', 'Drama',
    'Family', 'Fantasy', 'History', 'Horror', 'Kids', 'Music', 'Mystery', 'News',
    'Reality', 'Romance', 'Sci-Fi & Fantasy', 'Science Fiction', 'Soap', 'Sports',
    'Talk', 'Thriller', 'War & Politics', 'Western',
)
REGION_CHOICES = (
    ('US', 'United States'),
    ('CA', 'Canada'),
    ('GB', 'United Kingdom'),
    ('AU', 'Australia'),
    ('DE', 'Germany'),
    ('FR', 'France'),
    ('ES', 'Spain'),
    ('IT', 'Italy'),
    ('JP', 'Japan'),
)
REGION_CODES = {code for code, _label in REGION_CHOICES}
CATEGORY_ALIASES = {
    'soap opera': {'soap'},
    'soap operas': {'soap'},
}


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
    account_form = AccountProfileForm(initial={
        'first_name': request.user.first_name,
        'last_name': request.user.last_name,
        'email': request.user.email,
    })

    if request.method == 'POST':
        action = request.POST.get('action', 'discovery')
        if action == 'account':
            account_form = AccountProfileForm(request.POST)
            if account_form.is_valid():
                request.user.first_name = account_form.cleaned_data['first_name']
                request.user.last_name = account_form.cleaned_data['last_name']
                request.user.email = account_form.cleaned_data['email']
                request.user.save(update_fields=['first_name', 'last_name', 'email'])
                return redirect('profile')
        else:
            selected = [
                genre for genre in request.POST.getlist('preferred_genres')
                if genre in DISCOVERY_GENRES
            ]
            region = request.POST.get('region', 'US').upper()
            if region not in REGION_CODES:
                region = 'US'
            notify_new_releases = request.POST.get('notify_new_releases') == '1'
            if notify_new_releases and not request.user.email:
                notify_new_releases = False
            preference.preferred_genres = selected
            preference.customized = True
            preference.region = region
            preference.require_region_availability = request.POST.get('require_region_availability') == '1'
            preference.notify_new_releases = notify_new_releases
            preference.save(update_fields=[
                'preferred_genres', 'customized', 'region', 'require_region_availability',
                'notify_new_releases',
            ])
            return redirect('profile')

    selected = preference.preferred_genres if preference.customized else list(DISCOVERY_GENRES)
    return render(request, 'accounts/profile.html', {
        'account_form': account_form,
        'discovery_genres': DISCOVERY_GENRES,
        'preferred_genres': selected,
        'preferences_customized': preference.customized,
        'region_choices': REGION_CHOICES,
        'discovery_region': preference.region,
        'require_region_availability': preference.require_region_availability,
        'notify_new_releases': preference.notify_new_releases,
    })


def _expanded_category(value):
    normalized = str(value or '').strip().casefold()
    if not normalized:
        return set()
    return {normalized, *CATEGORY_ALIASES.get(normalized, set())}


def _filter_discovery(items, preferred_genres, customized=False):
    if not customized:
        return items
    wanted = set()
    for genre in preferred_genres:
        wanted.update(_expanded_category(genre))
    filtered = []
    for item in items:
        categories = set()
        for value in item.get('genres', []):
            categories.update(_expanded_category(value))
        show_type = str(item.get('show_type') or '').strip()
        if show_type:
            categories.update(_expanded_category(show_type))
        if item.get('is_news'):
            categories.add('news')
        if categories & wanted:
            filtered.append(item)
    return filtered


def _dedupe_discovery(items, seen=None):
    seen = seen if seen is not None else set()
    unique = []
    for item in items:
        key = (
            item.get('external_source') or item.get('source_type'),
            item.get('external_id') or item.get('id'),
            item.get('content_type'),
        )
        if key in seen:
            continue
        seen.add(key)
        unique.append(item)
    return unique


def _search_live_items(items, query='', content_type=''):
    query = query.casefold()
    results = []
    for item in items:
        if content_type and item.get('content_type') != content_type:
            continue
        if query:
            haystack = ' '.join([
                str(item.get('title') or ''),
                str(item.get('genre') or ''),
                str(item.get('description') or ''),
                str(item.get('network') or ''),
                str(item.get('provider') or ''),
            ]).casefold()
            if query not in haystack:
                continue
        results.append(item)
    return results


def home(request):
    preference = None
    if request.user.is_authenticated:
        preference, _ = DiscoveryPreference.objects.get_or_create(user=request.user)

    customized = bool(preference and preference.customized)
    preferred_genres = preference.preferred_genres if customized else list(DISCOVERY_GENRES)
    discovery_region = preference.region if preference else 'US'
    require_region_availability = bool(preference and preference.require_region_availability)

    live_tv = _filter_discovery(
        fetch_live_tv_schedule(limit=100, country=discovery_region),
        preferred_genres,
        customized=customized,
    )
    trending_tv = _filter_discovery(fetch_trending_tv(), preferred_genres, customized=customized)
    on_the_air_tv = _filter_discovery(fetch_tv_on_the_air(), preferred_genres, customized=customized)
    popular_tv = _filter_discovery(fetch_popular_tv(), preferred_genres, customized=customized)
    free_movies = fetch_free_archive_movies()
    trending_movies = _filter_discovery(fetch_trending_movies(), preferred_genres, customized=customized)

    seen_tmdb_tv = set()
    trending_tv = _dedupe_discovery(trending_tv, seen_tmdb_tv)
    on_the_air_tv = _dedupe_discovery(on_the_air_tv, seen_tmdb_tv)
    popular_tv = _dedupe_discovery(popular_tv, seen_tmdb_tv)

    saved_external_ids = {}
    if request.user.is_authenticated:
        saved_items = list(Watchlist.objects.filter(user=request.user).select_related('content'))
        saved_external_ids = {
            (entry.content.external_source, entry.content.external_id, entry.content.content_type): entry.content_id
            for entry in saved_items
            if entry.content.external_source and entry.content.external_id
        }

    live_sources = [
        *live_tv,
        *trending_tv,
        *on_the_air_tv,
        *popular_tv,
        *free_movies,
        *trending_movies,
    ]
    for item in live_sources:
        item['saved_content_id'] = saved_external_ids.get(
            (item.get('external_source'), item.get('external_id'), item.get('content_type'))
        )

    query = request.GET.get('q', '').strip()
    content_type = request.GET.get('type', '').strip()
    if content_type not in {'movie', 'tv'}:
        content_type = ''
    browse_active = bool(query or content_type)
    browse_results = _search_live_items(live_sources, query, content_type) if browse_active else []

    context = {
        'live_tv': live_tv,
        'trending_tv': trending_tv[:20],
        'on_the_air_tv': on_the_air_tv[:20],
        'popular_tv': popular_tv[:20],
        'free_movies': free_movies,
        'trending_movies': trending_movies[:10],
        'browse_active': browse_active,
        'browse_results': browse_results,
        'browse_query': request.GET.get('q', '').strip(),
        'browse_type': content_type,
        'preferences_customized': customized,
        'discovery_region': discovery_region,
        'require_region_availability': require_region_availability,
    }
    return render(request, 'home.html', context)
