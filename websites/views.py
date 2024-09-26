import requests

from bs4 import BeautifulSoup
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpRequest, HttpResponse, StreamingHttpResponse, HttpResponseRedirect, JsonResponse
from django.shortcuts import render
from django.urls import reverse_lazy
from django.views import generic
from urllib.parse import urljoin, urlparse, urlunparse

from django.views.decorators.csrf import csrf_exempt

from websites.models import Website
from websites.forms import WebsiteCreateUpdateForm
from websites.utils import update_links_and_forms, insert_base_tag


def index(request: HttpRequest) -> HttpResponse:
    return render(request, "index.html")


class WebsiteListView(LoginRequiredMixin, generic.ListView):
    model = Website
    paginate_by = 10
    template_name = "websites/list.html"

    def get_queryset(self):
        return Website.objects.filter(user=self.request.user)


class WebsiteCreationView(LoginRequiredMixin, generic.CreateView):
    model = Website
    template_name = "websites/create.html"
    form_class = WebsiteCreateUpdateForm
    success_url = reverse_lazy("websites:list")

    def form_valid(self, form):
        form.instance.user = self.request.user
        return super().form_valid(form)


class WebsiteUpdateView(LoginRequiredMixin, generic.UpdateView):
    model = Website
    template_name = "websites/create.html"
    form_class = WebsiteCreateUpdateForm
    success_url = reverse_lazy("websites:list")

    def get_queryset(self):
        return Website.objects.filter(user=self.request.user)


class WebsiteDeleteView(LoginRequiredMixin, generic.DeleteView):
    model = Website
    success_url = reverse_lazy("websites:list")

    def get_queryset(self):
        return Website.objects.filter(user=self.request.user)


def ensure_https(url):
    url = url.strip()
    parsed_url = urlparse(url)

    if not parsed_url.scheme:
        url = f"https://{url}"

    return url


def ensure_base_path(base_url, subpath):
    parsed_url = urlparse(base_url)
    base_url = urlunparse((parsed_url.scheme, parsed_url.netloc, '', '', '', ''))
    subpath = urljoin(parsed_url.path, subpath)

    return base_url, subpath


def get_website(request, website_name, base_url, url, headers, subpath):
    response = requests.get(url, headers=headers, stream=True)
    response.raise_for_status()

    if response.status_code == 200:
        soup = BeautifulSoup(response.content, 'html.parser')
        insert_base_tag(soup, url)

        update_links_and_forms(request, soup, base_url, website_name, subpath)

        return StreamingHttpResponse(
            str(soup),
            content_type=response.headers.get('content-type'),
            status=response.status_code,
            reason=response.reason
        )


def post_to_website(request, website_name, base_url, url, cors_headers, subpath):
    form_action = request.POST.get('form_action', url)
    post_data = {key: value.encode('utf-8') if isinstance(value, str) else value for key, value in request.POST.items()}

    post_headers = {
        key: value.encode('utf-8') if isinstance(value, str) else value
        for key, value in request.META.items()
        if key.startswith("HTTP")
    }

    post_headers.update(cors_headers)

    response = requests.post(form_action, data=post_data, headers=post_headers, stream=True)

    if response.status_code == 200:
        soup = BeautifulSoup(response.content, 'html.parser')
        insert_base_tag(soup, url)

        update_links_and_forms(request, soup, base_url, website_name, subpath)

        return StreamingHttpResponse(
            str(soup),
            content_type=response.headers.get('content-type'),
            status=response.status_code,
            reason=response.reason
        )
    else:
        return HttpResponse('Не вдалося обробити запит', status=response.status_code)


@csrf_exempt
@login_required
def vpn_website(request: HttpRequest, website_name: str, subpath: str = '') -> HttpResponse | StreamingHttpResponse:
    website = Website.objects.filter(user=request.user, name__iexact=website_name).first()

    if not website:
        return HttpResponse('У вас немає такого сайту. Добавте.', status=404)

    base_url = ensure_https(website.url)
    base_url, subpath = ensure_base_path(base_url, subpath)

    url = urljoin(base_url, subpath) if subpath else base_url

    headers = {
        'User-Agent': request.META.get('HTTP_USER_AGENT', 'Mozilla/5.0'),
        'Referer': base_url,
        'X-Requested-With': 'XMLHttpRequest',
    }

    cors_headers = {
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Methods': 'GET, POST, PATCH, PUT, DELETE, OPTIONS',
        'Access-Control-Allow-Headers': 'Origin, Content-Type, X-Auth-Token',
        'Content-Type': 'application/json; charset=UTF-8',
        'Access-Control-Max-Age': '86400',
    }

    headers.update(cors_headers)

    if request.method == "OPTIONS":
        return HttpResponse(status=204, headers=cors_headers)

    if request.method == "GET":
        return get_website(request, website_name, base_url, url, headers, subpath)

    elif request.method == "POST":
        return post_to_website(request, website_name, base_url, url, cors_headers, subpath)

    return HttpResponse('Де сторінка', status=404)
