from django.urls import path

from . import views

urlpatterns = [
    path("g/<int:group_id>/tables/new/", views.create_table, name="table_create"),
    path("g/<int:group_id>/presets/new/", views.preset_form, name="preset_create"),
    path("g/<int:group_id>/presets/<int:preset_id>/", views.preset_form, name="preset_edit"),
]
