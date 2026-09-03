from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from .models import ReleaseNotification


@login_required
def inbox(request):
    notifications = ReleaseNotification.objects.filter(user=request.user).select_related('content')[:100]
    unread_count = ReleaseNotification.objects.filter(user=request.user, read_at__isnull=True).count()
    return render(request, 'notifications/inbox.html', {
        'notifications': notifications,
        'unread_count': unread_count,
    })


@login_required
@require_POST
def mark_read(request, notification_id):
    notification = get_object_or_404(ReleaseNotification, id=notification_id, user=request.user)
    if notification.read_at is None:
        notification.read_at = timezone.now()
        notification.save(update_fields=['read_at'])
    return redirect('notifications:inbox')


@login_required
@require_POST
def mark_all_read(request):
    ReleaseNotification.objects.filter(user=request.user, read_at__isnull=True).update(read_at=timezone.now())
    return redirect('notifications:inbox')
