from django.contrib import admin
from django.urls import path

from viewer import views

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", views.index, name="index"),
    path("review", views.review, name="review"),
    path("reviews", views.review),  # alias
    # Folder management
    path("folders/add", views.add_folder, name="add_folder"),
    path("folders/<int:folder_id>/delete", views.delete_folder, name="delete_folder"),
    path("api/browse", views.browse, name="browse"),
    # Review API
    path("api/photos", views.photo_queue, name="photo_queue"),
    path("api/rate", views.rate, name="rate"),
    path("api/undo", views.undo, name="undo"),
    path("image", views.image, name="image"),
]
