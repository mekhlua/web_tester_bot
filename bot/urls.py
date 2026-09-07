from django.urls import path
from bot import views

urlpatterns = [
    path("new/", views.create_spec, name="create_spec"),
    path("spec/<int:spec_id>/", views.spec_detail, name="spec_detail"),
]