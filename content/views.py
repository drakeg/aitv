from decimal import Decimal, InvalidOperation
from urllib.parse import urlparse

from django.contrib.auth.decorators import login_required
from django.http import HttpResponseBadRequest, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_POST

from watchlist.models import Watchlist

from .forms import ContentAvailabilityFormSet, ContentItemForm
from .models import ContentItem


@login_required
def edit_content(request, content_id):
    item = get_object_or_404(ContentItem, id=content_id)
    if request.method == 'POST':
        form = ContentItemForm(request.POST, instance=item)
        has_availability_formset = 'availability-TOTAL_FORMS' in request.POST
        availability_formset = ContentAvailabilityFormSet(
            request.POST if has_availability_formset else None,
            instance=item,
            prefix='availability',
        )
        availability_valid = (
            availability_formset.is_valid() if has_availability_formset else True
        )
        if form.is_valid() and availability_valid:
            item = form.save()
            if has_availability_formset:
                availability_formset.instance = item
                availability_formset.save()
            return redirect('/')
    else:
        form = ContentItemForm(instance=item)
        availability_formset = ContentAvailabilityFormSet(
            instance=item,
            prefix='availability',
        )

    return render(
        request,
        'content/edit.html',
        {
            'form': form,
            'availability_formset': availability_formset,
            'item': item,
        },
    )


@login_required
@require_POST
def delete_content(request, content_id):
    item = get_object_or_404(ContentItem, id=content_id)
    item.delete()
    return redirect('/')


def _optional_int(value):
    value = str(value or '').strip()
    return int(value) if value.isdigit() else None


def _optional_rating(value):
    value = str(value or '').strip()
    if not value:
        return None
    try:
        rating = Decimal(value)
    except InvalidOperation:
        return None
    return rating if Decimal('0') <= rating <= Decimal('10') else None


@login_required
@require_POST
def import_external_content(request):
    title = request.POST.get('title', '').strip()
    url = request.POST.get('url', '').strip()
    thumbnail = request.POST.get('thumbnail', '').strip()
    content_type = request.POST.get('content_type', 'movie').strip()
    external_source = request.POST.get('external_source', '').strip()
    external_id = request.POST.get('external_id', '').strip()

    parsed = urlparse(url)
    valid_tmdb_host = parsed.hostname in {'themoviedb.org', 'www.themoviedb.org'}
    if (
        not title
        or parsed.scheme not in {'http', 'https'}
        or not valid_tmdb_host
        or content_type not in {ContentItem.ContentType.MOVIE, ContentItem.ContentType.TV}
        or external_source != 'tmdb'
        or not external_id.isdigit()
    ):
        return HttpResponseBadRequest('Invalid external content.')

    defaults = {
        'title': title,
        'genre': request.POST.get('genre', '').strip() or ('TV' if content_type == 'tv' else 'Movie'),
        'thumbnail': thumbnail or None,
        'source_type': 'tmdb',
        'content_type': content_type,
        'description': request.POST.get('description', '').strip(),
        'release_year': _optional_int(request.POST.get('release_year')),
        'rating': _optional_rating(request.POST.get('rating')),
        'external_source': 'tmdb',
        'external_id': external_id,
    }

    item = ContentItem.objects.filter(
        external_source='tmdb',
        external_id=external_id,
        content_type=content_type,
    ).first()
    if item:
        for field, value in defaults.items():
            setattr(item, field, value)
        item.url = url
        item.save()
    else:
        item = ContentItem.objects.create(url=url, **defaults)

    Watchlist.objects.get_or_create(user=request.user, content=item)
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({
            'saved': True,
            'content_id': item.id,
            'remove_url': reverse('watchlist:remove', args=[item.id]),
            'label': '✓ Saved to Watchlist',
        })
    return redirect('/')
