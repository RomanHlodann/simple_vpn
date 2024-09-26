from urllib.parse import urljoin
from django.urls.base import reverse


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

            print(tag['href'])

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

            print(tag['action'])
        elif tag.name == 'script' or tag.name == 'link':
            print()


def insert_base_tag(soup, url):
    base_tag = soup.new_tag('base', href=url)
    if soup.head:
        soup.head.insert(0, base_tag)
    else:
        head_tag = soup.new_tag('head')
        head_tag.insert(0, base_tag)
        soup.insert(0, head_tag)
