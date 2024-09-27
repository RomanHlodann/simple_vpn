import re

from urllib.parse import urljoin, urlencode, urlunparse, urlparse
from bs4 import BeautifulSoup
from django.urls.base import reverse

from websites.models import Website


def update_links(request, tag, tag_attr, parsed_base_url, main_domain, subpath, website_name):
    tag[tag_attr] = tag[tag_attr].replace(r'\/', '/')
    tag[tag_attr] = tag[tag_attr].replace(r'/\\', '/')
    parsed_url = urlparse(tag[tag_attr])
    domain = f"{parsed_base_url.scheme}://{parsed_url.netloc}"
    if main_domain in domain:
        tag[tag_attr] = tag[tag_attr][len(domain):]

    if tag[tag_attr].startswith('https:'):
        return

    new_href = urljoin(subpath, tag[tag_attr])
    if new_href and new_href[0] != '/':
        new_href = '/' + new_href
    tag[tag_attr] = request.build_absolute_uri(reverse("websites:get_website", args=[website_name, new_href]))


def update_links_and_forms(request, soup, url, website_name, subpath):
    parsed_base_url = urlparse(url)
    main_domain = f"{parsed_base_url.netloc}"

    for tag in soup.find_all(['a', 'form', 'script']):
        if tag.name == 'a' and tag.has_attr('href'):
            update_links(request, tag, 'href', parsed_base_url, main_domain, subpath, website_name)

        elif tag.name == 'form' and tag.has_attr('action'):
            update_links(request, tag, 'action', parsed_base_url, main_domain, subpath, website_name)


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
