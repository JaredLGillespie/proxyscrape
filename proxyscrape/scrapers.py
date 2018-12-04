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

__all__ = ['Proxy', 'ProxyResource', 'RESOURCE_MAP', 'RESOURCE_TYPE_MAP']


from bs4 import BeautifulSoup
from collections import namedtuple
from threading import Lock
import requests
import time

from .errors import InvalidHTMLError, RequestNotOKError


Proxy = namedtuple('Proxy', ['host', 'port', 'code', 'country', 'anonymous', 'type', 'source'])


class ProxyResource:
    """A manager for a single proxy resource.

    :param func:
        The scraping function.
    :param refresh_interval:
        The minimum time (in seconds) between each refresh.
    :type url: string
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
                except (InvalidHTMLError, RequestNotOKError):
                    pass

        return False, None


def get_anonymous_proxies():
    url = 'https://free-proxy-list.net/anonymous-proxy.html'
    response = requests.get(url)
    if not response.ok:
        raise RequestNotOKError()

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
    response = requests.get(url)
    if not response.ok:
        raise RequestNotOKError()

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
    content = element.find('div').text
    rows = content.replace('"', '').replace("'", '').split('\n')

    proxies = set()
    for row in rows:
        row = row.strip()
        if len(row) == 0:
            continue

        params = row.split(':')
        params.extend([None, None, None, type, source])
        proxies.add(Proxy(*params))
    return proxies


def get_proxy_daily_http_proxies():
    url = 'http://www.proxy-daily.com'
    response = requests.get(url)
    if not response.ok:
        raise RequestNotOKError()

    try:
        soup = BeautifulSoup(response.content, 'html.parser')
        content = soup.find('div', {'id': 'free-proxy-list'})
        centers = content.find_all('center')
        return _get_proxy_daily_proxies_parse_inner(centers[0], 'http', 'proxy-daily-http')
    except (AttributeError, KeyError):
        raise InvalidHTMLError()


def get_proxy_daily_socks4_proxies():
    url = 'http://www.proxy-daily.com'
    response = requests.get(url)
    if not response.ok:
        raise RequestNotOKError()

    try:
        soup = BeautifulSoup(response.content, 'html.parser')
        content = soup.find('div', {'id': 'free-proxy-list'})
        centers = content.find_all('center')
        return _get_proxy_daily_proxies_parse_inner(centers[1], 'socks4', 'proxy-daily-socks4')
    except (AttributeError, KeyError):
        raise InvalidHTMLError()


def get_proxy_daily_socks5_proxies():
    url = 'http://www.proxy-daily.com'
    response = requests.get(url)
    if not response.ok:
        raise RequestNotOKError()

    try:
        soup = BeautifulSoup(response.content, 'html.parser')
        content = soup.find('div', {'id': 'free-proxy-list'})
        centers = content.find_all('center')
        return _get_proxy_daily_proxies_parse_inner(centers[2], 'socks5', 'proxy-daily-socks5')
    except (AttributeError, KeyError):
        raise InvalidHTMLError()


def get_socks_proxies():
    url = 'https://www.socks-proxy.net'
    response = requests.get(url)
    if not response.ok:
        raise RequestNotOKError()

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
    response = requests.get(url)
    if not response.ok:
        raise RequestNotOKError()

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
    response = requests.get(url)
    if not response.ok:
        raise RequestNotOKError()

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


def get_us_proxies():
    url = 'https://www.us-proxy.org'
    response = requests.get(url)
    if not response.ok:
        raise RequestNotOKError()

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


RESOURCE_MAP = {
    'anonymous-proxy': get_anonymous_proxies,
    'free-proxy-list': get_free_proxy_list_proxies,
    'proxy-daily-http': get_proxy_daily_http_proxies,
    'proxy-daily-socks4': get_proxy_daily_socks4_proxies,
    'proxy-daily-socks5': get_proxy_daily_socks5_proxies,
    'socks-proxy': get_socks_proxies,
    'ssl-proxy': get_ssl_proxies,
    'uk-proxy': get_uk_proxies,
    'us-proxy': get_us_proxies
}

RESOURCE_TYPE_MAP = {
    'http': {
        'us-proxy',
        'uk-proxy',
        'free-proxy-list',
        'proxy-daily-http',
        'anonymous-proxy'
    },
    'https': {
        'us-proxy',
        'uk-proxy',
        'free-proxy-list',
        'ssl-proxy',
        'anonymous-proxy'
    },
    'socks4': {
        'socks-proxy',
        'proxy-daily-socks4'
    },
    'socks5': {
        'socks-proxy',
        'proxy-daily-socks5'
    }
}
