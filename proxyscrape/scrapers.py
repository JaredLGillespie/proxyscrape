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

from bs4 import BeautifulSoup
from collections import namedtuple
from threading import Lock
import requests
import re
import time


_Proxy = namedtuple('Proxy', ['host', 'port', 'country', 'anonymous', 'https', 'version', 'source'])


class ProxyResource:
    def __init__(self, url, func, refresh_interval):
        self.url = url
        self.func = func
        self.refresh_interval = refresh_interval
        self.lock = Lock()
        self.last_refresh_time = 0

    def refresh(self):
        if self.last_refresh_time + self.refresh_interval < time.time():
            return False, None

        with self.lock:
            # Check if updated before
            if self.last_refresh_time + self.refresh_interval < time.time():
                proxies = self.func(self.url)
                self.last_refresh_time = time.time()
                return True, proxies

        return False, None


def _get_proxy_daily_proxies_parse_inner(str):
    inner_reg = re.findall(r'''
            ([0-9]{1,3}\. # Host Address
            [0-9]{1,3}\.
            [0-9]{1,3}\.
            [0-9]{1,3}
            :[0-9]{1,5}) # Port Number
        ''', str, re.X | re.S)

    if inner_reg:
        return {_Proxy(*i.split(':'), None, None, None, None, 'proxy-daily')
                for i in inner_reg}
    return set()


def get_proxy_daily_proxies_http(str):
    outer_reg = re.findall(r'''
        Free\sHttp/Https\sProxy\sList 
        .*
        Free\sSocks4\sProxy\sList
    ''', str, re.X | re.S)

    if outer_reg:
        return _get_proxy_daily_proxies_parse_inner(outer_reg[0])
    return set()


def get_proxy_daily_proxies_socks4(str):
    outer_reg = re.findall(r'''
         Free\sSocks4\sProxy\sList
        .*
        Free\sSocks5\sProxy\sList
    ''', str, re.X | re.S)

    if outer_reg:
        return _get_proxy_daily_proxies_parse_inner(outer_reg[0])
    return set()


def get_proxy_daily_proxies_socks5(str):
    outer_reg = re.findall(r'''
         Free\sSocks5\sProxy\sList
        .*
    ''', str, re.X | re.S)

    if outer_reg:
        return _get_proxy_daily_proxies_parse_inner(outer_reg[0])
    return set()


def get_us_proxy_proxies(url):
    response = requests.get(url)
    soup = BeautifulSoup(response.content, 'html.parser')
    table = soup.find('table', {'id': 'proxylisttable'})
    proxies = set()

    for row in table.find_all('tr'):
        rows = list(map(lambda x: x.text, row))
        host = rows[0]
        port = rows[1]
        country = rows[3].lower()
        anonymous = rows[4].lower() in ('anonymous', 'elite proxy')
        https = rows[6].lower() == 'yes'

        proxies.add(_Proxy(host, port, country, anonymous, https, None, 'us-proxy'))

    return proxies


def get_uk_proxy_proxies(url):
    response = requests.get(url)
    soup = BeautifulSoup(response.content, 'html.parser')
    table = soup.find('table', {'id': 'proxylisttable'})
    proxies = set()

    for row in table.find_all('tr'):
        rows = list(map(lambda x: x.text, row))
        host = rows[0]
        port = rows[1]
        country = rows[3].lower()
        anonymous = rows[4].lower() in ('anonymous', 'elite proxy')
        https = rows[6].lower() == 'yes'

        proxies.add(_Proxy(host, port, country, anonymous, https, None, 'uk-proxy'))

    return proxies


def get_free_proxy_list_proxies(url):
    response = requests.get(url)
    soup = BeautifulSoup(response.content, 'html.parser')
    table = soup.find('table', {'id': 'proxylisttable'})
    proxies = set()

    for row in table.find_all('tr'):
        rows = list(map(lambda x: x.text, row))
        host = rows[0]
        port = rows[1]
        country = rows[3].lower()
        anonymous = rows[4].lower() in ('anonymous', 'elite proxy')
        https = rows[6].lower() == 'yes'

        proxies.add(_Proxy(host, port, country, anonymous, https, None, 'free-proxy-list'))

    return proxies


def get_socks_proxy_proxies(url):
    response = requests.get(url)
    soup = BeautifulSoup(response.content, 'html.parser')
    table = soup.find('table', {'id': 'proxylisttable'})
    proxies = set()

    for row in table.find_all('tr'):
        rows = list(map(lambda x: x.text, row))
        host = rows[0]
        port = rows[1]
        country = rows[3].lower()
        version = rows[4].lower()
        anonymous = rows[5].lower() in ('anonymous', 'elite proxy')
        https = rows[6].lower() == 'yes'

        proxies.add(_Proxy(host, port, country, anonymous, https, version, 'socks-proxy'))

    return proxies


def get_ssl_proxy_proxies(url):
    response = requests.get(url)
    soup = BeautifulSoup(response.content, 'html.parser')
    table = soup.find('table', {'id': 'proxylisttable'})
    proxies = set()

    for row in table.find_all('tr'):
        rows = list(map(lambda x: x.text, row))
        host = rows[0]
        port = rows[1]
        country = rows[3].lower()
        anonymous = rows[4].lower() in ('anonymous', 'elite proxy')
        https = rows[6].lower() == 'yes'

        proxies.add(_Proxy(host, port, country, anonymous, https, None, 'ssl-proxy'))

    return proxies


RESOURCE_MAP = {
    'socks-proxy': {
        'url': 'https://www.socks-proxy.net',
        'func': get_socks_proxy_proxies
    },
    'ssl-proxy': {
        'url': 'https://www.sslproxies.org/',
        'func': get_ssl_proxy_proxies
    },
    'us-proxy': {
        'url': 'https://www.us-proxy.org',
        'func': get_us_proxy_proxies,
    },
    'uk-proxy': {
        'url': 'https://free-proxy-list.net/uk-proxy.html',
        'func': get_uk_proxy_proxies
    },
    'free-proxy-list': {
        'url': 'http://www.free-proxy-list.net',
        'func': get_free_proxy_list_proxies
    },
    'proxy-daily-http': {
        'url': 'http://www.proxy-daily.com',
        'func': get_proxy_daily_proxies_http
    },
    'proxy-daily-socks4': {
        'url': 'http://www.proxy-daily.com',
        'func': get_proxy_daily_proxies_socks4
    },
    'proxy-daily-socks5': {
        'url': 'http://www.proxy-daily.com',
        'func': get_proxy_daily_proxies_socks5
    }
}


RESOURCE_TYPE_MAP = {
    'http': {
        'us-proxy',
        'uk-proxy',
        'free-proxy-list',
        'proxy-daily-http'
    },
    'https': {
        'us-proxy',
        'uk-proxy',
        'free-proxy-list',
        'proxy-daily-http',
        'ssl-proxy'
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
