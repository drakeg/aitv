from django.urls import path

from . import views

app_name = 'content'

urlpatterns = [
    path('<int:content_id>/edit/', views.edit_content, name='edit'),
    path('<int:content_id>/delete/', views.delete_content, name='delete'),
    path('import/', views.import_external_content, name='import_external'),
]
