from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.urls import include, path

from core.views import home, live_tv_guide, profile, register, toggle_channel_favorite

urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/login/', auth_views.LoginView.as_view(template_name='registration/login.html'), name='login'),
    path('accounts/logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('accounts/register/', register, name='register'),
    path('accounts/profile/', profile, name='profile'),
    path('live-tv/', live_tv_guide, name='live_tv_guide'),
    path('live-tv/channels/<int:channel_id>/favorite/', toggle_channel_favorite, name='toggle_channel_favorite'),
    path('content/', include('content.urls')),
    path('watchlist/', include('watchlist.urls')),
    path('notifications/', include('notifications.urls')),
    path('', home, name='home'),
]
