
from django.contrib import admin
from django.urls import include,path
from core.views import home

urlpatterns = [
    path('admin/', admin.site.urls),
    path('watchlist/', include('watchlist.urls')),
    path('', home),
]
