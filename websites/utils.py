import re

from urllib.parse import urljoin, urlencode, urlunparse, urlparse
from bs4 import BeautifulSoup
from django.urls.base import reverse

from websites.models import Website



def update_links_and_forms(request, soup, url, website_name, subpath):
    for tag in soup.find_all(['a', 'form', 'script']):
        if tag.name == 'a' and tag.has_attr('href'):
            if tag['href'].startswith(url):
                tag['href'] = tag['href'][len(url):]

            if tag['href'].startswith('https:'):
                continue

            new_href = urljoin(subpath, tag['href'])
            if new_href and new_href[0] != '/':
                new_href = '/' + new_href
            tag['href'] = request.build_absolute_uri(reverse("websites:get_website", args=[website_name, new_href]))


        elif tag.name == 'form' and tag.has_attr('action'):
            if tag['action'].startswith(url):
                tag['action'] = tag['action'][len(url):]

            if tag['action'].startswith('https:'):
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

        elif tag.name == 'script':
            if tag.string:

                original_script = tag.string

                original_script = original_script.replace(r'\/', '/')

                urls = re.findall(r'https?://[^\s\'"<>]+|(/[^\s\'"<>]+)', original_script)

                def change_url(match):
                    url_to_modify = match.group(0)
                    if url_to_modify.startswith(url):
                        url_to_modify = url_to_modify[len(url):]

                    if url_to_modify.startswith("http"):
                        base_url = reverse('websites:get_source')
                        query_params = urlencode({'path': url_to_modify, 'website_name': website_name})
                        full_url = f"{base_url}?{query_params}"
                        return request.build_absolute_uri(full_url)

                    if url_to_modify and url_to_modify[0] != '/':
                        url_to_modify = '/' + url_to_modify

                    return request.build_absolute_uri(
                        reverse("websites:get_website", args=[website_name, url_to_modify])
                    )

                modified_script = re.sub(
                    r'https?://[^\s\'"<>]+|(/[^\s\'"<>]+)',  # Regex to find URLs
                    lambda match: change_url(match),  # Call change_url for each match
                    original_script
                )

                tag.string = modified_script

                u = 1


def insert_base_tag(soup, url):
    base_tag = soup.new_tag('base', href=url)
    if soup.head:
        soup.head.insert(0, base_tag)
    else:
        head_tag = soup.new_tag('head')
        head_tag.insert(0, base_tag)
        soup.insert(0, head_tag)


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


def filter_headers(headers):
    hop_by_hop_headers = [
        'connection', 'keep-alive', 'proxy-authenticate', 'proxy-authorization',
        'te', 'trailer', 'transfer-encoding', 'upgrade'
    ]
    return {key: value for key, value in headers.items() if key.lower() not in hop_by_hop_headers}


def create_correct_soup(request, response, base_url, website_name, subpath, url=None):
    soup = BeautifulSoup(response.content, 'html.parser')
    if url:
        insert_base_tag(soup, url)
    update_links_and_forms(request, soup, base_url, website_name, subpath)
    return soup


def find_website(request, website_name):
    website = Website.objects.filter(user=request.user, name__iexact=website_name).first()
    if not website:
        return None
    return website


def get_baseurl_and_path(website, subpath):
    base_url = ensure_https(website.url)
    return ensure_base_path(base_url, subpath)