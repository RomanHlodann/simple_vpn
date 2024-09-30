import requests
import cloudscraper

from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpRequest, HttpResponse, StreamingHttpResponse
from django.shortcuts import render
from django.urls import reverse_lazy
from django.views import generic
from urllib.parse import urljoin
from django.views.decorators.csrf import csrf_exempt

from websites.models import Website
from websites.forms import WebsiteCreateUpdateForm
from websites.utils import filter_headers, create_correct_soup, find_website, get_baseurl_and_path


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


session = cloudscraper.create_scraper()


def get_website(request, website, base_url, url, subpath):
    response = session.get(url, stream=True)
    response.raise_for_status()

    if response.status_code == 200:
        soup = create_correct_soup(request, response, base_url, website.name, subpath, url)
        filtered_headers = filter_headers(response.headers)

        filtered_headers['Content-Type'] = 'text/html; charset=utf-8'

        website.transition_count += 1
        website.bytes_count += len(str(soup))
        website.save()

        return StreamingHttpResponse(
            str(soup),
            headers=filtered_headers,
            status=response.status_code,
            reason=response.reason
        )


def post_to_website(request, website, base_url, url, subpath):
    post_data = {key: value for key, value in request.POST.items()}
    response = session.post(url, data=post_data, stream=True)

    filtered_headers = filter_headers(response.headers)

    if response.status_code == 200:
        soup = create_correct_soup(request, response, base_url, website.name, subpath, url)

        return StreamingHttpResponse(
            str(soup),
            headers=filtered_headers,
            status=response.status_code,
            reason=response.reason
        )
    else:
        return HttpResponse('Не вдалося обробити запит', status=response.status_code)


@csrf_exempt
@login_required
def vpn_website(request: HttpRequest, website_name: str, subpath: str = '') -> HttpResponse | StreamingHttpResponse:
    website = find_website(request, website_name)

    if not website:
        return HttpResponse('У вас немає такого сайту. Добавте.', status=404)

    base_url, subpath = get_baseurl_and_path(website, subpath)
    url = urljoin(base_url, subpath) if subpath else base_url

    if request.method == "OPTIONS":
        return requests.options(url, stream=True)

    if request.method == "GET":
        return get_website(request, website, base_url, url, subpath)

    elif request.method == "POST":
        return post_to_website(request, website, base_url, url, subpath)

    return HttpResponse('Де сторінка', status=404)
