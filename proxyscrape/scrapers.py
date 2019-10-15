# MIT License
#
# Copyright (c) 2018 Jared Gillespie
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

__all__ = ['add_resource', 'add_resource_type', 'get_resources', 'get_resource_types', 'ProxyResource', 'RESOURCE_MAP',
           'RESOURCE_TYPE_MAP']


from bs4 import BeautifulSoup
from threading import Lock
import time
from collections import OrderedDict
from urllib.parse import urljoin

from .errors import (
    InvalidHTMLError,
    InvalidResourceError,
    InvalidResourceTypeError,
    RequestNotOKError,
    RequestFailedError,
    ResourceAlreadyDefinedError,
    ResourceTypeAlreadyDefinedError
)
from .shared import (
    is_iterable,
    Proxy,
    request_proxy_list
)
_resource_lock = Lock()
_resource_type_lock = Lock()


class ProxyResource:
    """A manager for a single proxy resource.

    :param func:
        The scraping function.
    :param refresh_interval:
        The minimum time (in seconds) between each refresh.
    :type func: function
    :type refresh_interval: int
    """
    def __init__(self, func, refresh_interval):
        self._func = func
        self._refresh_interval = refresh_interval
        self._lock = Lock()
        self._last_refresh_time = 0

    def refresh(self, force=False):
        """Refreshes proxies.

        Proxies are refreshed if they haven't been refreshed within the past `refresh_interval`, or if `force` is True.

      :param force:
            Whether to force a refresh. If True, a refresh is always performed; otherwise it is only done if a refresh
            hasn't occurred within the collector's `refresh_interval`. Defaults to False.
        :return:
            A tuple denoting whether proxies were refreshed and the proxies retrieved.
        :rtype: (bool, iterable)
        """
        if not force and self._last_refresh_time + self._refresh_interval > time.time():
            return False, None

        with self._lock:
            # Check if updated before
            if force or self._last_refresh_time + self._refresh_interval <= time.time():

                try:
                    proxies = self._func()
                    self._last_refresh_time = time.time()
                    return True, proxies
                except (InvalidHTMLError, RequestNotOKError, RequestFailedError):
                    pass

        return False, None


def get_anonymous_proxies():
    url = 'https://free-proxy-list.net/anonymous-proxy.html'
    response = request_proxy_list(url)

    try:
        soup = BeautifulSoup(response.content, 'html.parser')
        table = soup.find('table', {'id': 'proxylisttable'})
        proxies = set()

        for row in table.find('tbody').find_all('tr'):
            data = list(map(lambda x: x.text, row.find_all('td')))
            host = data[0]
            port = data[1]
            code = data[2].lower()
            country = data[3].lower()
            anonymous = data[4].lower() in ('anonymous', 'elite proxy')
            version = 'https' if data[6].lower() == 'yes' else 'http'

            proxies.add(Proxy(host, port, code, country, anonymous, version, 'anonymous-proxy'))

        return proxies
    except (AttributeError, KeyError):
        raise InvalidHTMLError()


def get_free_proxy_list_proxies():
    url = 'http://www.free-proxy-list.net'
    response = request_proxy_list(url)

    try:
        soup = BeautifulSoup(response.content, 'html.parser')
        table = soup.find('table', {'id': 'proxylisttable'})
        proxies = set()

        for row in table.find('tbody').find_all('tr'):
            data = list(map(lambda x: x.text, row.find_all('td')))
            host = data[0]
            port = data[1]
            code = data[2].lower()
            country = data[3].lower()
            anonymous = data[4].lower() in ('anonymous', 'elite proxy')
            version = 'https' if data[6].lower() == 'yes' else 'http'

            proxies.add(Proxy(host, port, code, country, anonymous, version, 'free-proxy-list'))

        return proxies
    except (AttributeError, KeyError):
        raise InvalidHTMLError()


def _get_proxy_daily_proxies_parse_inner(element, type, source):
    content = element.contents[0]
    rows = content.replace('"', '').replace("'", '').split('\n')

    proxies = set()
    for row in rows:
        row = row.strip()
        if len(row) == 0:
            continue

        params = str(row).split(':')
        params.extend([None, None, None, type, source])
        proxies.add(Proxy(*params))
    return proxies


def get_proxy_daily_data_elements():
    url = 'http://www.proxy-daily.com'
    response = request_proxy_list(url)

    try:
        soup = BeautifulSoup(response.content, 'html.parser')
        content = soup.find('div', {'id': 'free-proxy-list'})
        return content.find_all(class_="freeProxyStyle")
    except (AttributeError, KeyError):
        raise InvalidHTMLError()


def get_proxy_daily_http_proxies():
    http_data_element = get_proxy_daily_data_elements()[0]
    return _get_proxy_daily_proxies_parse_inner(http_data_element, 'http', 'proxy-daily-http')


def get_proxy_daily_socks4_proxies():
    socks4_data_element = get_proxy_daily_data_elements()[1]
    return _get_proxy_daily_proxies_parse_inner(socks4_data_element, 'socks4', 'proxy-daily-socks4')


def get_proxy_daily_socks5_proxies():
    socks5_data_element = get_proxy_daily_data_elements()[2]
    return _get_proxy_daily_proxies_parse_inner(socks5_data_element, 'socks5', 'proxy-daily-socks5')


def get_socks_proxies():
    url = 'https://www.socks-proxy.net'
    response = request_proxy_list(url)

    try:
        soup = BeautifulSoup(response.content, 'html.parser')
        table = soup.find('table', {'id': 'proxylisttable'})
        proxies = set()

        for row in table.find('tbody').find_all('tr'):
            data = list(map(lambda x: x.text, row.find_all('td')))
            host = data[0]
            port = data[1]
            code = data[2].lower()
            country = data[3].lower()
            version = data[4].lower()
            anonymous = data[5].lower() in ('anonymous', 'elite proxy')

            proxies.add(Proxy(host, port, code, country, anonymous, version, 'socks-proxy'))

        return proxies
    except (AttributeError, KeyError):
        raise InvalidHTMLError()


def get_ssl_proxies():
    url = 'https://www.sslproxies.org/'
    response = request_proxy_list(url)

    try:
        soup = BeautifulSoup(response.content, 'html.parser')
        table = soup.find('table', {'id': 'proxylisttable'})
        proxies = set()

        for row in table.find('tbody').find_all('tr'):
            data = list(map(lambda x: x.text, row.find_all('td')))
            host = data[0]
            port = data[1]
            code = data[2].lower()
            country = data[3].lower()
            anonymous = data[4].lower() in ('anonymous', 'elite proxy')

            proxies.add(Proxy(host, port, code, country, anonymous, 'https', 'ssl-proxy'))

        return proxies
    except (AttributeError, KeyError):
        raise InvalidHTMLError()


def get_uk_proxies():
    url = 'https://free-proxy-list.net/uk-proxy.html'
    response = request_proxy_list(url)

    try:
        soup = BeautifulSoup(response.content, 'html.parser')
        table = soup.find('table', {'id': 'proxylisttable'})
        proxies = set()

        for row in table.find('tbody').find_all('tr'):
            data = list(map(lambda x: x.text, row.find_all('td')))
            host = data[0]
            port = data[1]
            code = data[2].lower()
            country = data[3].lower()
            anonymous = data[4].lower() in ('anonymous', 'elite proxy')
            version = 'https' if data[6].lower() == 'yes' else 'http'

            proxies.add(Proxy(host, port, code, country, anonymous, version, 'uk-proxy'))

        return proxies
    except (AttributeError, KeyError):
        raise InvalidHTMLError()


def get_spys_one(verbose=False):
    def parse_dict(script):
        rows = script.split(";")
        new_rows = {}
        for row in rows:
            if not '=' in row:
                continue
            cells = row.split("=")
            if "^" in cells[1]:
                subcells = cells[1].split("^")
                subcells[1] = new_rows[subcells[1]]
                new_rows[cells[0]] = eval(subcells[0] + "^" + subcells[1], {"__builtins__": None}, {})
            else:
                new_rows[cells[0]] = cells[1]
        return OrderedDict(sorted(new_rows.items(), key=lambda x: len(x[0]), reverse=True))

    def parse(soup, source):
        proxies = set()
        Anonymities = {'ANM', 'HIA'}
        ports_dict = parse_dict(soup.select("script")[3].text)
        trs = soup.select("tr.spy1xx, tr.spy1x")
        for row in trs:
            cells = row.select("td")
            if not '.' in cells[0].text:
                continue
            protocol = cells[1].text.split(" ")[0].lower()
            host = cells[0].text.split("<", 1)[0].split("document")[0]
            port = cells[0].find("script").text.split("+", 1)[1]
            for key in ports_dict:
                port = port.replace(key, str(ports_dict[key]))
            port = eval("(" + port.replace("(", "str("), {"__builtins__": None}, {'str': str})
            code = None
            country = cells[3].find("a").text
            anonymous = cells[2].text in Anonymities
            proxies.add(Proxy(host, port, code, country, anonymous, protocol, source))
        return proxies

    proxies = set()
    base_url = 'http://spys.one/en/free-proxy-list/'
    # http://spys.one/en/https-ssl-proxy/ is not supported yet
    urls = {'http://spys.one/en/free-proxy-list/', 'http://spys.one/en/anonymous-proxy-list/',
            'http://spys.one/en/non-anonymous-proxy-list/', 'http://spys.one/en/socks-proxy-list/', 'http://spys.one/en/http-proxy-list/'}
    for url in urls:
        status = True
        while status:
            response = request_proxy_list(url)
            try:
                soup = BeautifulSoup(response.text, 'html.parser')
                proxies = proxies.union(parse(soup, 'spys-one'))
                font = soup.select("font.spy14")[0]
                status = 'Next' in font.text
                if status:
                    url = font.find_parent("a")['href']
                    url = urljoin(base_url, url)
            except (AttributeError, KeyError):
                raise InvalidHTMLError()
    return proxies


def get_proxynova():
    def parse(soup):
        table = soup.find('table', {'id': 'tbl_proxy_list'})
        proxies = set()
        protocol = "http"
        for row in table.find('tbody').find_all('tr'):
            cells = row.find_all('td')
            if not cells[0].find("abbr"):
                continue
            parts = cells[0].find("abbr").text.split("'")
            host = parts[1][8:] + parts[3]
            port = cells[1].text.strip()
            code = cells[5].find("img")['alt'].lower()
            country = cells[5].find("a").text.split("\t")[0].lower()

            anonymous = cells[6].find("span").text.lower() in ('anonymous', 'elite')
            proxies.add(Proxy(host, port, code, country, anonymous, protocol, 'proxynova'))
        return proxies
    url = 'https://www.proxynova.com/proxy-server-list/'
    proxies = set()
    urls = set()
    response = request_proxy_list(url)
    soup = BeautifulSoup(response.content, 'html.parser')
    for a in soup.select("a"):
        try:
            if 'country-' in a['href'] and int(a.find("span").text[1:-1]) > 0:
                urls.add(urljoin(url, a['href']))
        except:
            pass

    status = True
    while status:
        try:
            proxies = proxies.union(parse(soup))
            status = len(urls)
            if status:
                url = urls.pop()
                response = request_proxy_list(url)
                soup = BeautifulSoup(response.content, 'html.parser')
        except (AttributeError, KeyError):
            raise InvalidHTMLError()
    return proxies


def get_us_proxies():
    url = 'https://www.us-proxy.org'
    response = request_proxy_list(url)

    try:
        soup = BeautifulSoup(response.content, 'html.parser')
        table = soup.find('table', {'id': 'proxylisttable'})
        proxies = set()

        for row in table.find('tbody').find_all('tr'):
            data = list(map(lambda x: x.text, row.find_all('td')))
            host = data[0]
            port = data[1]
            code = data[2].lower()
            country = data[3].lower()
            anonymous = data[4].lower() in ('anonymous', 'elite proxy')
            version = 'https' if data[6].lower() == 'yes' else 'http'

            proxies.add(Proxy(host, port, code, country, anonymous, version, 'us-proxy'))

        return proxies
    except (AttributeError, KeyError):
        raise InvalidHTMLError()


def add_resource(name, func, resource_types=None):
    """Adds a new resource, which is representative of a function that scrapes a particular set of proxies.

    :param name:
        An identifier for the resource.
    :param func:
        The scraping function.
    :param resource_types:
        (optional) The resource types to add the resource to. Can either be a single or sequence of resource types.
    :type name: string
    :type func: function
    :type resource_types: iterable or string or None
    :raises InvalidResourceTypeError:
        If 'resource_types' is defined are does not represent defined resource types.
    :raises ResourceAlreadyDefinedError:
        If 'name' is already a defined resource.
    """
    if name in RESOURCE_MAP:
        raise ResourceAlreadyDefinedError('{} is already defined as a resource'.format(name))

    if resource_types is not None:
        if not is_iterable(resource_types):
            resource_types = {resource_types, }

        for resource_type in resource_types:
            if resource_type not in RESOURCE_TYPE_MAP:
                raise InvalidResourceTypeError(
                    '{} is not a defined resource type'.format(resource_type))

    with _resource_lock:
        # Ensure not added by the time entered lock
        if name in RESOURCE_MAP:
            raise ResourceAlreadyDefinedError('{} is already defined as a resource'.format(name))

        RESOURCE_MAP[name] = func

        if resource_types is not None:
            for resource_type in resource_types:
                RESOURCE_TYPE_MAP[resource_type].add(name)


def add_resource_type(name, resources=None):
    """Adds a new resource type, which is a representative of a group of resources.

    :param name:
        An identifier for the resource type.
    :param resources:
        (optional) The resources to add to the resource type. Can either be a single or sequence of resources.
    :type name: string
    :type resources: string or iterable
    :raises InvalidResourceError:
        If any of the resources are invalid.
    :raises ResourceTypeAlreadyDefinedError:
        If 'name' is already a defined resource type.
    """
    if name in RESOURCE_TYPE_MAP:
        raise ResourceTypeAlreadyDefinedError(
            '{} is already defined as a resource type'.format(name))

    with _resource_type_lock:
        # Ensure not added by the time entered lock
        if name in RESOURCE_TYPE_MAP:
            raise ResourceTypeAlreadyDefinedError(
                '{} is already defined as a resource type'.format(name))

        if resources is not None:
            if not is_iterable(resources):
                resources = {resources, }
            resources = set(resources)

            for resource in resources:
                if resource not in RESOURCE_MAP:
                    raise InvalidResourceError('{} is an invalid resource'.format(resource))
        else:
            resources = set()

        RESOURCE_TYPE_MAP[name] = resources


def get_resource_types():
    """Returns a set of the resource types.

    :return:
        The defined resource types.
    :rtype: set
    """
    return set(RESOURCE_TYPE_MAP.keys())


def get_resources():
    """Returns a set of the resources.

    :return:
        The defined resources.
    :rtype: set
    """
    return set(RESOURCE_MAP.keys())


RESOURCE_MAP = {
    'anonymous-proxy': get_anonymous_proxies,
    'free-proxy-list': get_free_proxy_list_proxies,
    'proxy-daily-http': get_proxy_daily_http_proxies,
    'proxy-daily-socks4': get_proxy_daily_socks4_proxies,
    'proxy-daily-socks5': get_proxy_daily_socks5_proxies,
    'socks-proxy': get_socks_proxies,
    'ssl-proxy': get_ssl_proxies,
    'uk-proxy': get_uk_proxies,
    'us-proxy': get_us_proxies,
    'spys-one': get_spys_one,
    'proxynova': get_proxynova
}

RESOURCE_TYPE_MAP = {
    'http': {
        'us-proxy',
        'uk-proxy',
        'free-proxy-list',
        'proxy-daily-http',
        'anonymous-proxy',
        'spys-one',
        'proxynova'
    },
    'https': {
        'us-proxy',
        'uk-proxy',
        'free-proxy-list',
        'ssl-proxy',
        'anonymous-proxy',
        'spys-one'
    },
    'socks4': {
        'socks-proxy',
        'proxy-daily-socks4'
    },
    'socks5': {
        'socks-proxy',
        'proxy-daily-socks5',
        'spys-one'
    }
}
