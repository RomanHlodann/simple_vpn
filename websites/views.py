import requests

from bs4 import BeautifulSoup
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpRequest, HttpResponse, StreamingHttpResponse, HttpResponseRedirect, JsonResponse
from django.shortcuts import render
from django.urls import reverse_lazy
from django.urls.base import reverse
from django.views import generic
from urllib.parse import urljoin, urlparse, urlencode

from django.views.decorators.csrf import csrf_exempt

from websites.models import Website
from websites.forms import WebsiteCreateUpdateForm


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


@csrf_exempt
@login_required
def get_website(request: HttpRequest, website_name: str, subpath: str = '') -> HttpResponse | StreamingHttpResponse:
    website = Website.objects.filter(user=request.user, name__iexact=website_name).first()

    if not website:
        return HttpResponse('У вас немає такого сайту. Добавте.', status=404)

    base_url = ensure_https(website.url)
    url = urljoin(base_url, subpath) if subpath else base_url

    headers = {
        'User-Agent': request.META.get('HTTP_USER_AGENT', 'Mozilla/5.0'),
        'Referer': base_url,
        'X-Requested-With': 'XMLHttpRequest',
    }

    cors_headers = {
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
        'Access-Control-Allow-Headers': 'Content-Type, Authorization',
    }

    headers.update(cors_headers)

    if request.method == "OPTIONS":
        return HttpResponse(status=204, headers=cors_headers)

    if request.method == "GET":
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

    elif request.method == "POST":
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

    return HttpResponse('Де сторінка', status=404)


def insert_base_tag(soup, url):
    base_tag = soup.new_tag('base', href=url)
    if soup.head:
        soup.head.insert(0, base_tag)
    else:
        head_tag = soup.new_tag('head')
        head_tag.insert(0, base_tag)
        soup.insert(0, head_tag)


def update_links_and_forms(request, soup, url, website_name, subpath):
    for tag in soup.find_all(['a', 'form']):
        if tag.name == 'a' and tag.has_attr('href'):
            if url in tag['href']:
                tag['href'] = tag['href'][len(url):]

            if 'https:' in tag['href']:
                continue

            new_href = urljoin(subpath, tag['href'])
            if new_href and new_href[0] != '/':
                new_href = '/' + new_href
            tag['href'] = request.build_absolute_uri(reverse("websites:get_website", args=[website_name, new_href]))

        elif tag.name == 'form' and tag.has_attr('action'):
            if url in tag['action']:
                tag['action'] = tag['action'][len(url):]

            if 'https:' in tag['action']:
                continue

            new_action = urljoin(subpath, tag['action'])
            if new_action and new_action[0] != '/':
                new_action = '/' + new_action
            tag['action'] = request.build_absolute_uri(reverse("websites:get_website", args=[website_name, new_action]))

            csrf_token = request.POST.get('csrfmiddlewaretoken') or request.COOKIES.get('csrftoken')
            if csrf_token:
                csrf_input = soup.new_tag('input', type='hidden', attrs={
                    'name': 'csrfmiddlewaretoken',
                    'value': csrf_token
                })
                tag.append(csrf_input)
