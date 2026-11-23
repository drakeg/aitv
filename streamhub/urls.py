from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.urls import include, path

from core.views import health_live, health_ready, home, live_tv_channel_schedule, live_tv_guide, operator_dashboard, operator_guest_launch_sheet, operator_guest_qr, profile, register, toggle_channel_favorite

urlpatterns = [
    path('health/live/', health_live, name='health_live'),
    path('health/ready/', health_ready, name='health_ready'),
    path('admin/', admin.site.urls),
    path('operator/', operator_dashboard, name='operator_dashboard'),
    path('operator/guest-launch-sheet/', operator_guest_launch_sheet, name='operator_guest_launch_sheet'),
    path('operator/guest-qr/<str:target>/', operator_guest_qr, name='operator_guest_qr'),
    path('accounts/login/', auth_views.LoginView.as_view(template_name='registration/login.html'), name='login'),
    path('accounts/logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('accounts/register/', register, name='register'),
    path('accounts/profile/', profile, name='profile'),
    path('live-tv/', live_tv_guide, name='live_tv_guide'),
    path('live-tv/channels/<int:channel_id>/', live_tv_channel_schedule, name='live_tv_channel_schedule'),
    path('live-tv/channels/<int:channel_id>/favorite/', toggle_channel_favorite, name='toggle_channel_favorite'),
    path('content/', include('content.urls')),
    path('watchlist/', include('watchlist.urls')),
    path('notifications/', include('notifications.urls')),
    path('', home, name='home'),
]
