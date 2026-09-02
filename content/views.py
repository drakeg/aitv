from urllib.parse import urlparse

from django.contrib.auth.decorators import login_required
from django.http import HttpResponseBadRequest
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from .forms import ContentItemForm
from .models import ContentItem


@login_required
def edit_content(request, content_id):
    item = get_object_or_404(ContentItem, id=content_id)
    if request.method == 'POST':
        form = ContentItemForm(request.POST, instance=item)
        if form.is_valid():
            form.save()
            return redirect('/')
    else:
        form = ContentItemForm(instance=item)

    return render(request, 'content/edit.html', {'form': form, 'item': item})


@login_required
@require_POST
def delete_content(request, content_id):
    item = get_object_or_404(ContentItem, id=content_id)
    item.delete()
    return redirect('/')


@login_required
@require_POST
def import_external_content(request):
    title = request.POST.get('title', '').strip()
    url = request.POST.get('url', '').strip()
    thumbnail = request.POST.get('thumbnail', '').strip()

    parsed = urlparse(url)
    if not title or parsed.scheme not in {'http', 'https'} or parsed.hostname not in {
        'themoviedb.org',
        'www.themoviedb.org',
    }:
        return HttpResponseBadRequest('Invalid external content.')

    item, _ = ContentItem.objects.update_or_create(
        url=url,
        defaults={
            'title': title,
            'genre': request.POST.get('genre', 'Movie').strip() or 'Movie',
            'thumbnail': thumbnail or None,
            'source_type': 'movie',
        },
    )
    return redirect('/')
