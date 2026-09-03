from django.urls import path

from . import views

app_name = 'watchlist'

urlpatterns = [
    path('', views.watchlist, name='list'),
    path('add/<int:content_id>/', views.add_to_watchlist, name='add'),
    path('remove/<int:content_id>/', views.remove_from_watchlist, name='remove'),
]
