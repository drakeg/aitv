from django.urls import path
from . import views

urlpatterns = [
    path('add/<int:content_id>/', views.add_to_watchlist, name='add_to_watchlist'),
    path('remove/<int:content_id>/', views.remove_from_watchlist, name='remove_from_watchlist'),
]
