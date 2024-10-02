from django.urls import path, include
from users.views import (
    UserCreationView,
    UserDetailView,
    UserUpdateView
)


urlpatterns = [
    path("", include("django.contrib.auth.urls")),
    path("register/", UserCreationView.as_view(), name="register"),
    path("me/", UserDetailView.as_view(), name="detail"),
    path("me/edit/", UserUpdateView.as_view(), name="update"),
]

app_name = "users"
