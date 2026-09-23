from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils.http import url_has_allowed_host_and_scheme
from django.utils import timezone
from django.views.decorators.http import require_POST

from .models import ReleaseNotification


def _safe_inbox_return(request):
    next_url = request.POST.get('next', '')
    if next_url and url_has_allowed_host_and_scheme(
        url=next_url,
        allowed_hosts={request.get_host()},
        require_https=request.is_secure(),
    ):
        return next_url
    return reverse('notifications:inbox')


@login_required
def inbox(request):
    notification_list = ReleaseNotification.objects.filter(user=request.user).select_related('content')
    page_obj = Paginator(notification_list, 25).get_page(request.GET.get('page'))
    page_range = page_obj.paginator.get_elided_page_range(number=page_obj.number)
    return render(request, 'notifications/inbox.html', {
        'notifications': page_obj.object_list,
        'page_obj': page_obj,
        'page_range': page_range,
    })


@login_required
@require_POST
def mark_read(request, notification_id):
    notification = get_object_or_404(ReleaseNotification, id=notification_id, user=request.user)
    if notification.read_at is None:
        notification.read_at = timezone.now()
        notification.save(update_fields=['read_at'])
    return redirect(_safe_inbox_return(request))


@login_required
@require_POST
def mark_all_read(request):
    ReleaseNotification.objects.filter(user=request.user, read_at__isnull=True).update(read_at=timezone.now())
    return redirect(_safe_inbox_return(request))
