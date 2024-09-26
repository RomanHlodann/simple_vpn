from django.urls import path, re_path
from websites.views import (
    index,
    WebsiteListView,
    WebsiteCreationView,
    WebsiteUpdateView,
    WebsiteDeleteView,
    vpn_website,
)


urlpatterns = [
    path("", index, name="index"),
    path("websites/", WebsiteListView.as_view(), name="list"),
    path("websites/create/", WebsiteCreationView.as_view(), name="create"),
    path("websites/<int:pk>/update/", WebsiteUpdateView.as_view(), name="update"),
    path("websites/<int:pk>/delete/", WebsiteDeleteView.as_view(), name="delete"),
    re_path(r'^(?P<website_name>[^/]+)/?(?P<subpath>.*)?$', vpn_website, name='get_website'),
]


app_name = "websites"
