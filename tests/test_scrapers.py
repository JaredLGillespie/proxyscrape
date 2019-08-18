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

import os
import sys
import time
from threading import Thread
import unittest
try:
    from unittest.mock import Mock, patch
except ImportError:
    from mock import Mock, patch

from proxyscrape.errors import (
    InvalidResourceError,
    InvalidResourceTypeError,
    ResourceAlreadyDefinedError,
    ResourceTypeAlreadyDefinedError
)
from proxyscrape.scrapers import (
    add_resource,
    add_resource_type,
    get_resources,
    get_resource_types,
    _resource_lock,
    _resource_type_lock,
    ProxyResource,
    RESOURCE_MAP
)
import proxyscrape.scrapers as pss
from proxyscrape.shared import Proxy

RESOURCE_MAP_COPY = pss.RESOURCE_MAP.copy()
RESOURCE_TYPE_MAP_COPY = {k: v.copy() for k, v in pss.RESOURCE_TYPE_MAP.items()}


def hold_lock(lock, hold_time, func):
    with lock:
        time.sleep(hold_time)
        func()


def get_random_resource_name(self):
    return self._testMethodName + '-resource'


def get_random_resource_type_name(self):
    return self._testMethodName + '-resource-type'


class TestProxyResource(unittest.TestCase):
    def test_refreshes_if_expired(self):
        expected = [Proxy('host', 'port', 'code', 'country', 'anonymous', 'type', 'source')]

        def func():
            return expected

        pr = ProxyResource(func, -1)

        refreshed, actual = pr.refresh()
        self.assertEqual(True, refreshed)
        self.assertEqual(expected[0], actual[0])

        refreshed, actual = pr.refresh()
        self.assertEqual(True, refreshed)
        self.assertEqual(expected[0], actual[0])

    def test_doesnt_refresh_if_not_expired(self):
        expected = [Proxy('host', 'port', 'code', 'country', 'anonymous', 'type', 'source')]

        def func():
            return expected

        pr = ProxyResource(func, 5)

        refreshed, actual = pr.refresh()
        self.assertEqual(True, refreshed)
        self.assertEqual(expected[0], actual[0])

        refreshed, actual = pr.refresh()
        self.assertEqual(False, refreshed)
        self.assertEqual(None, actual)

    def test_refreshes_if_forced(self):
        expected = [Proxy('host', 'port', 'code', 'country', 'anonymous', 'type', 'source')]

        def func():
            return expected

        pr = ProxyResource(func, 5)

        refreshed, actual = pr.refresh()
        self.assertEqual(True, refreshed)
        self.assertEqual(expected[0], actual[0])

        refreshed, actual = pr.refresh(True)
        self.assertEqual(True, refreshed)
        self.assertEqual(expected[0], actual[0])

    def test_doesnt_refresh_if_lock_check(self):
        expected = [Proxy('host', 'port', 'code', 'country', 'anonymous', 'type', 'source')]

        def func():
            return expected

        pr = ProxyResource(func, 5)

        refreshed, actual = pr.refresh()
        self.assertEqual(True, refreshed)
        self.assertEqual(expected[0], actual[0])

        with patch('proxyscrape.scrapers.time') as time_mock:
            times = [time.time() + 10, -1, 0]
            time_iter = iter(times)
            time_mock.time = lambda: next(time_iter)

            refreshed, actual = pr.refresh()
            self.assertEqual(False, refreshed)
            self.assertIsNone(actual)


class TestScrapers(unittest.TestCase):
    def setUp(self):
        self.requests_patcher = patch('proxyscrape.shared.requests')
        self.requests = self.requests_patcher.start()

    def tearDown(self):
        self.requests_patcher.stop()

    def test_anonymous_proxies_success(self):
        with open(os.path.join(cwd, 'mock_pages', 'anonymous-proxy.html'), 'r') as html:
            response = Mock()
            response.content = html
            response.ok = True
            self.requests.get = lambda url: response

            expected = {
                Proxy('179.124.59.232', '53281', 'br', 'brazil', True, 'https', 'anonymous-proxy'),
                Proxy('200.107.59.98', '8080', 'ua', 'ukraine', True, 'http', 'anonymous-proxy'),
                Proxy('217.172.244.7', '8080', 'ru', 'russian federation', True, 'http', 'anonymous-proxy')
            }

            func = RESOURCE_MAP['anonymous-proxy']
            pr = ProxyResource(func, 10)

            _, proxies = pr.refresh()

            for proxy in proxies:
                self.assertIn(proxy, expected)

    def test_anonymous_proxies_not_ok(self):
        response = Mock()
        response.ok = False
        self.requests.get = lambda url: response

        func = RESOURCE_MAP['anonymous-proxy']
        pr = ProxyResource(func, 10)

        refreshed, proxies = pr.refresh()

        self.assertEqual(False, refreshed)
        self.assertIsNone(proxies)

    def test_anonymous_proxies_request_exception(self):
        def raise_exception(url):
            raise self.requests.RequestException()

        self.requests.RequestException = Exception
        self.requests.get = raise_exception

        func = RESOURCE_MAP['anonymous-proxy']
        pr = ProxyResource(func, 10)

        refreshed, proxies = pr.refresh()

        self.assertEqual(False, refreshed)
        self.assertIsNone(proxies)

    def test_anonymous_proxies_invalid_html(self):
        with open(os.path.join(cwd, 'mock_pages', 'empty.html'), 'r') as html:
            response = Mock()
            response.content = html
            response.ok = True
            self.requests.get = lambda url: response

            func = RESOURCE_MAP['anonymous-proxy']
            pr = ProxyResource(func, 10)

            refreshed, proxies = pr.refresh()

            self.assertEqual(False, refreshed)
            self.assertIsNone(proxies)

    def test_free_proxy_list_proxies_success(self):
        with open(os.path.join(cwd, 'mock_pages', 'free-proxy-list-proxy.html'), 'r') as html:
            response = Mock()
            response.content = html
            response.ok = True
            self.requests.get = lambda url: response

            expected = {
                Proxy('179.124.59.232', '53281', 'br', 'brazil', True, 'https', 'free-proxy-list'),
                Proxy('200.107.59.98', '8080', 'ua', 'ukraine', False, 'http', 'free-proxy-list'),
                Proxy('217.172.244.7', '8080', 'ru', 'russian federation', True, 'http', 'free-proxy-list')
            }

            func = RESOURCE_MAP['free-proxy-list']
            pr = ProxyResource(func, 10)

            _, proxies = pr.refresh()

            for proxy in proxies:
                self.assertIn(proxy, expected)

    def test_free_proxy_list_proxies_not_ok(self):
        response = Mock()
        response.ok = False
        self.requests.get = lambda url: response

        func = RESOURCE_MAP['free-proxy-list']
        pr = ProxyResource(func, 10)

        refreshed, proxies = pr.refresh()

        self.assertEqual(False, refreshed)
        self.assertIsNone(proxies)

    def test_free_proxy_list_proxies_request_exception(self):
        def raise_exception(url):
            raise self.requests.RequestException()

        self.requests.RequestException = Exception
        self.requests.get = raise_exception

        func = RESOURCE_MAP['free-proxy-list']
        pr = ProxyResource(func, 10)

        refreshed, proxies = pr.refresh()

        self.assertEqual(False, refreshed)
        self.assertIsNone(proxies)

    def test_free_proxy_list_proxies_invalid_html(self):
        with open(os.path.join(cwd, 'mock_pages', 'empty.html'), 'r') as html:
            response = Mock()
            response.content = html
            response.ok = True
            self.requests.get = lambda url: response

            func = RESOURCE_MAP['free-proxy-list']
            pr = ProxyResource(func, 10)

            refreshed, proxies = pr.refresh()

            self.assertEqual(False, refreshed)
            self.assertIsNone(proxies)

    def test_proxy_daily_http_proxies_success(self):
        with open(os.path.join(cwd, 'mock_pages', 'proxy-daily-proxy.html'), 'r') as html:
            response = Mock()
            response.content = html
            response.ok = True
            self.requests.get = lambda url: response

            expected = {
                Proxy('93.190.253.50', '80', None, None, None, 'http', 'proxy-daily-http'),
                Proxy('207.154.231.209', '3128', None, None, None, 'http', 'proxy-daily-http'),
                Proxy('88.255.101.177', '53281', None, None, None, 'http', 'proxy-daily-http')
            }

            func = RESOURCE_MAP['proxy-daily-http']
            pr = ProxyResource(func, 10)

            _, proxies = pr.refresh()

            for proxy in proxies:
                self.assertIn(proxy, expected)

    def test_proxy_daily_http_proxies_not_ok(self):
        response = Mock()
        response.ok = False
        self.requests.get = lambda url: response

        func = RESOURCE_MAP['proxy-daily-http']
        pr = ProxyResource(func, 10)

        refreshed, proxies = pr.refresh()

        self.assertEqual(False, refreshed)
        self.assertIsNone(proxies)

    def test_proxy_daily_http_proxies_request_exception(self):
        def raise_exception(url):
            raise self.requests.RequestException()

        self.requests.RequestException = Exception
        self.requests.get = raise_exception

        func = RESOURCE_MAP['proxy-daily-http']
        pr = ProxyResource(func, 10)

        refreshed, proxies = pr.refresh()

        self.assertEqual(False, refreshed)
        self.assertIsNone(proxies)

    def test_proxy_daily_http_proxies_invalid_html(self):
        with open(os.path.join(cwd, 'mock_pages', 'empty.html'), 'r') as html:
            response = Mock()
            response.content = html
            response.ok = True
            self.requests.get = lambda url: response

            func = RESOURCE_MAP['proxy-daily-http']
            pr = ProxyResource(func, 10)

            refreshed, proxies = pr.refresh()

            self.assertEqual(False, refreshed)
            self.assertIsNone(proxies)

    def test_proxy_daily_socks4_proxies_success(self):
        with open(os.path.join(cwd, 'mock_pages', 'proxy-daily-proxy.html'), 'r') as html:
            response = Mock()
            response.content = html
            response.ok = True
            self.requests.get = lambda url: response

            expected = {
                Proxy('54.38.156.185', '8888', None, None, None, 'socks4', 'proxy-daily-socks4'),
                Proxy('194.85.174.74', '1080', None, None, None, 'socks4', 'proxy-daily-socks4'),
                Proxy('41.79.237.135', '1080', None, None, None, 'socks4', 'proxy-daily-socks4')
            }

            func = RESOURCE_MAP['proxy-daily-socks4']
            pr = ProxyResource(func, 10)

            _, proxies = pr.refresh()

            for proxy in proxies:
                self.assertIn(proxy, expected)

    def test_proxy_daily_socks4_proxies_not_ok(self):
        response = Mock()
        response.ok = False
        self.requests.get = lambda url: response

        func = RESOURCE_MAP['proxy-daily-socks4']
        pr = ProxyResource(func, 10)

        refreshed, proxies = pr.refresh()

        self.assertEqual(False, refreshed)
        self.assertIsNone(proxies)

    def test_proxy_daily_socks4_proxies_request_exception(self):
        def raise_exception(url):
            raise self.requests.RequestException()

        self.requests.RequestException = Exception
        self.requests.get = raise_exception

        func = RESOURCE_MAP['proxy-daily-socks4']
        pr = ProxyResource(func, 10)

        refreshed, proxies = pr.refresh()

        self.assertEqual(False, refreshed)
        self.assertIsNone(proxies)

    def test_proxy_daily_socks4_proxies_invalid_html(self):
        with open(os.path.join(cwd, 'mock_pages', 'empty.html'), 'r') as html:
            response = Mock()
            response.content = html
            response.ok = True
            self.requests.get = lambda url: response

            func = RESOURCE_MAP['proxy-daily-socks4']
            pr = ProxyResource(func, 10)

            refreshed, proxies = pr.refresh()

            self.assertEqual(False, refreshed)
            self.assertIsNone(proxies)

    def test_proxy_daily_socks5_proxies_success(self):
        with open(os.path.join(cwd, 'mock_pages', 'proxy-daily-proxy.html'), 'r') as html:
            response = Mock()
            response.content = html
            response.ok = True
            self.requests.get = lambda url: response

            expected = {
                Proxy('176.9.19.170', '1080', None, None, None, 'socks5', 'proxy-daily-socks5'),
                Proxy('188.26.83.105', '1080', None, None, None, 'socks5', 'proxy-daily-socks5'),
                Proxy('150.129.151.44', '6667', None, None, None, 'socks5', 'proxy-daily-socks5')
            }

            func = RESOURCE_MAP['proxy-daily-socks5']
            pr = ProxyResource(func, 10)

            _, proxies = pr.refresh()

            for proxy in proxies:
                self.assertIn(proxy, expected)

    def test_proxy_daily_socks5_proxies_not_ok(self):
        response = Mock()
        response.ok = False
        self.requests.get = lambda url: response

        func = RESOURCE_MAP['proxy-daily-socks5']
        pr = ProxyResource(func, 10)

        refreshed, proxies = pr.refresh()

        self.assertEqual(False, refreshed)
        self.assertIsNone(proxies)

    def test_proxy_daily_socks5_proxies_request_exception(self):
        def raise_exception(url):
            raise self.requests.RequestException()

        self.requests.RequestException = Exception
        self.requests.get = raise_exception

        func = RESOURCE_MAP['proxy-daily-socks5']
        pr = ProxyResource(func, 10)

        refreshed, proxies = pr.refresh()

        self.assertEqual(False, refreshed)
        self.assertIsNone(proxies)

    def test_proxy_daily_socks5_proxies_invalid_html(self):
        with open(os.path.join(cwd, 'mock_pages', 'empty.html'), 'r') as html:
            response = Mock()
            response.content = html
            response.ok = True
            self.requests.get = lambda url: response

            func = RESOURCE_MAP['proxy-daily-socks5']
            pr = ProxyResource(func, 10)

            refreshed, proxies = pr.refresh()

            self.assertEqual(False, refreshed)
            self.assertIsNone(proxies)

    def test_socks_proxy_proxies_success(self):
        with open(os.path.join(cwd, 'mock_pages', 'socks-proxy.html'), 'r') as html:
            response = Mock()
            response.content = html
            response.ok = True
            self.requests.get = lambda url: response

            expected = {
                Proxy('179.124.59.232', '53281', 'br', 'brazil', True, 'socks4', 'socks-proxy'),
                Proxy('200.107.59.98', '8080', 'ua', 'ukraine', True, 'socks5', 'socks-proxy'),
                Proxy('217.172.244.7', '8080', 'ru', 'russian federation', True, 'socks4', 'socks-proxy')
            }

            func = RESOURCE_MAP['socks-proxy']
            pr = ProxyResource(func, 10)

            _, proxies = pr.refresh()

            for proxy in proxies:
                self.assertIn(proxy, expected)

    def test_socks_proxies_not_ok(self):
        response = Mock()
        response.ok = False
        self.requests.get = lambda url: response

        func = RESOURCE_MAP['socks-proxy']
        pr = ProxyResource(func, 10)

        refreshed, proxies = pr.refresh()

        self.assertEqual(False, refreshed)
        self.assertIsNone(proxies)

    def test_socks_proxies_request_exception(self):
        def raise_exception(url):
            raise self.requests.RequestException()

        self.requests.RequestException = Exception
        self.requests.get = raise_exception

        func = RESOURCE_MAP['socks-proxy']
        pr = ProxyResource(func, 10)

        refreshed, proxies = pr.refresh()

        self.assertEqual(False, refreshed)
        self.assertIsNone(proxies)

    def test_socks_proxies_invalid_html(self):
        with open(os.path.join(cwd, 'mock_pages', 'empty.html'), 'r') as html:
            response = Mock()
            response.content = html
            response.ok = True
            self.requests.get = lambda url: response

            func = RESOURCE_MAP['socks-proxy']
            pr = ProxyResource(func, 10)

            refreshed, proxies = pr.refresh()

            self.assertEqual(False, refreshed)
            self.assertIsNone(proxies)

    def test_ssl_proxies_success(self):
        with open(os.path.join(cwd, 'mock_pages', 'ssl-proxy.html'), 'r') as html:
            response = Mock()
            response.content = html
            response.ok = True
            self.requests.get = lambda url: response

            expected = {
                Proxy('179.124.59.232', '53281', 'br', 'brazil', True, 'https', 'ssl-proxy'),
                Proxy('200.107.59.98', '8080', 'ua', 'ukraine', True, 'https', 'ssl-proxy'),
                Proxy('217.172.244.7', '8080', 'ru', 'russian federation', False, 'https', 'ssl-proxy')
            }

            func = RESOURCE_MAP['ssl-proxy']
            pr = ProxyResource(func, 10)

            _, proxies = pr.refresh()

            for proxy in proxies:
                self.assertIn(proxy, expected)

    def test_ssl_proxies_not_ok(self):
        response = Mock()
        response.ok = False
        self.requests.get = lambda url: response

        func = RESOURCE_MAP['ssl-proxy']
        pr = ProxyResource(func, 10)

        refreshed, proxies = pr.refresh()

        self.assertEqual(False, refreshed)
        self.assertIsNone(proxies)

    def test_ssl_proxies_request_exception(self):
        def raise_exception(url):
            raise self.requests.RequestException()

        self.requests.RequestException = Exception
        self.requests.get = raise_exception

        func = RESOURCE_MAP['ssl-proxy']
        pr = ProxyResource(func, 10)

        refreshed, proxies = pr.refresh()

        self.assertEqual(False, refreshed)
        self.assertIsNone(proxies)

    def test_ssl_proxies_invalid_html(self):
        with open(os.path.join(cwd, 'mock_pages', 'empty.html'), 'r') as html:
            response = Mock()
            response.content = html
            response.ok = True
            self.requests.get = lambda url: response

            func = RESOURCE_MAP['ssl-proxy']
            pr = ProxyResource(func, 10)

            refreshed, proxies = pr.refresh()

            self.assertEqual(False, refreshed)
            self.assertIsNone(proxies)

    def test_uk_proxies_success(self):
        with open(os.path.join(cwd, 'mock_pages', 'uk-proxy.html'), 'r') as html:
            response = Mock()
            response.content = html
            response.ok = True
            self.requests.get = lambda url: response

            expected = {
                Proxy('179.124.59.232', '53281', 'uk', 'united kingdom', True, 'https', 'uk-proxy'),
                Proxy('200.107.59.98', '8080', 'uk', 'united kingdom', True, 'http', 'uk-proxy'),
                Proxy('217.172.244.7', '8080', 'uk', 'united kingdom', False, 'http', 'uk-proxy')
            }

            func = RESOURCE_MAP['uk-proxy']
            pr = ProxyResource(func, 10)

            _, proxies = pr.refresh()

            for proxy in proxies:
                self.assertIn(proxy, expected)

    def test_uk_proxies_not_ok(self):
        response = Mock()
        response.ok = False
        self.requests.get = lambda url: response

        func = RESOURCE_MAP['uk-proxy']
        pr = ProxyResource(func, 10)

        refreshed, proxies = pr.refresh()

        self.assertEqual(False, refreshed)
        self.assertIsNone(proxies)

    def test_uk_proxies_request_exception(self):
        def raise_exception(url):
            raise self.requests.RequestException()

        self.requests.RequestException = Exception
        self.requests.get = raise_exception

        func = RESOURCE_MAP['uk-proxy']
        pr = ProxyResource(func, 10)

        refreshed, proxies = pr.refresh()

        self.assertEqual(False, refreshed)
        self.assertIsNone(proxies)

    def test_uk_proxies_invalid_html(self):
        with open(os.path.join(cwd, 'mock_pages', 'empty.html'), 'r') as html:
            response = Mock()
            response.content = html
            response.ok = True
            self.requests.get = lambda url: response

            func = RESOURCE_MAP['uk-proxy']
            pr = ProxyResource(func, 10)

            refreshed, proxies = pr.refresh()

            self.assertEqual(False, refreshed)
            self.assertIsNone(proxies)

    def test_us_proxies_success(self):
        with open(os.path.join(cwd, 'mock_pages', 'us-proxy.html'), 'r') as html:
            response = Mock()
            response.content = html
            response.ok = True
            self.requests.get = lambda url: response

            expected = {
                Proxy('179.124.59.232', '53281', 'us', 'united states', True, 'https', 'us-proxy'),
                Proxy('200.107.59.98', '8080', 'us', 'united states', True, 'http', 'us-proxy'),
                Proxy('217.172.244.7', '8080', 'us', 'united states', False, 'http', 'us-proxy')
            }

            func = RESOURCE_MAP['us-proxy']
            pr = ProxyResource(func, 10)

            _, proxies = pr.refresh()

            for proxy in proxies:
                self.assertIn(proxy, expected)

    def test_us_proxies_not_ok(self):
        response = Mock()
        response.ok = False
        self.requests.get = lambda url: response

        func = RESOURCE_MAP['us-proxy']
        pr = ProxyResource(func, 10)

        refreshed, proxies = pr.refresh()

        self.assertEqual(False, refreshed)
        self.assertIsNone(proxies)

    def test_us_proxies_request_exception(self):
        def raise_exception(url):
            raise self.requests.RequestException()

        self.requests.RequestException = Exception
        self.requests.get = raise_exception

        func = RESOURCE_MAP['us-proxy']
        pr = ProxyResource(func, 10)

        refreshed, proxies = pr.refresh()

        self.assertEqual(False, refreshed)
        self.assertIsNone(proxies)

    def test_us_proxies_invalid_html(self):
        with open(os.path.join(cwd, 'mock_pages', 'empty.html'), 'r') as html:
            response = Mock()
            response.content = html
            response.ok = True
            self.requests.get = lambda url: response

            func = RESOURCE_MAP['us-proxy']
            pr = ProxyResource(func, 10)

            refreshed, proxies = pr.refresh()

            self.assertEqual(False, refreshed)
            self.assertIsNone(proxies)


class TestResource(unittest.TestCase):
    def setUp(self):
        # Revert constants to defaults before each test
        pss.RESOURCE_MAP = RESOURCE_MAP_COPY.copy()
        pss.RESOURCE_TYPE_MAP = {k: v.copy() for k, v in RESOURCE_TYPE_MAP_COPY.items()}
        self.resource_name = get_random_resource_name(self)
        self.resource_type_name = get_random_resource_type_name(self)

    def test_add_resource_exception_if_duplicate(self):
        add_resource(self.resource_name, lambda: set(), 'http')

        with self.assertRaises(ResourceAlreadyDefinedError):
            add_resource(self.resource_name, lambda: set(), 'http')

    def test_add_resource_exception_if_invalid_resource_type(self):
        with self.assertRaises(InvalidResourceTypeError):
            add_resource(self.resource_name, lambda: set(), 'invalid')

    def test_add_resource_exception_if_duplicate_lock_check(self):
        # Intermittent failure in Python 2.7
        if sys.version_info.major < 3:
            return

        def func(): pss.RESOURCE_MAP[self.resource_name] = {}
        t = Thread(target=hold_lock, args=(_resource_lock, 0.1, func))
        t.start()

        with self.assertRaises(ResourceAlreadyDefinedError):
            add_resource(self.resource_name, lambda: set(), 'http')

        t.join()

    def test_add_resource_single_resource_type(self):
        add_resource(self.resource_name, lambda: set(), 'http')

        self.assertIn(self.resource_name, pss.RESOURCE_MAP)
        self.assertIn(self.resource_name, pss.RESOURCE_TYPE_MAP['http'])

    def test_add_resource_multiple_resource_types(self):
        add_resource(self.resource_name, lambda: set(), ['http', 'socks4'])

        self.assertIn(self.resource_name, pss.RESOURCE_MAP)
        self.assertIn(self.resource_name, pss.RESOURCE_TYPE_MAP['http'])
        self.assertIn(self.resource_name, pss.RESOURCE_TYPE_MAP['socks4'])

    def test_add_resource_none_resource_types(self):
        add_resource(self.resource_name, lambda: set(), None)
        self.assertIn(self.resource_name, pss.RESOURCE_MAP)

    def test_add_resource_type_exception_if_duplicate(self):
        add_resource_type(self.resource_type_name)

        with self.assertRaises(ResourceTypeAlreadyDefinedError):
            add_resource_type(self.resource_type_name)

    def test_add_resource_type_exception_if_duplicate_lock_check(self):
        # Intermittent failure in Python 2.7
        if sys.version_info.major < 3:
            return

        def func(): pss.RESOURCE_TYPE_MAP[self.resource_type_name] = set()
        t = Thread(target=hold_lock, args=(_resource_type_lock, 0.1, func))
        t.start()

        with self.assertRaises(ResourceTypeAlreadyDefinedError):
            add_resource_type(self.resource_type_name)

        t.join()

    def test_add_resource_type_adds_if_new(self):
        add_resource_type(self.resource_type_name)
        self.assertIn(self.resource_type_name, pss.RESOURCE_TYPE_MAP)

    def test_add_resource_single_resource(self):
        add_resource_type(self.resource_type_name, 'us-proxy')
        self.assertIn(self.resource_type_name, pss.RESOURCE_TYPE_MAP)
        self.assertSetEqual({'us-proxy'}, pss.RESOURCE_TYPE_MAP[self.resource_type_name])

    def test_add_resource_type_multiple_resources(self):
        add_resource_type(self.resource_type_name, ('us-proxy', 'uk-proxy'))
        self.assertIn(self.resource_type_name, pss.RESOURCE_TYPE_MAP)
        self.assertSetEqual({'us-proxy', 'uk-proxy'}, pss.RESOURCE_TYPE_MAP[self.resource_type_name])

    def test_add_resource_type_exception_if_invalid_resource(self):
        with self.assertRaises(InvalidResourceError):
            add_resource_type(self.resource_type_name, self.resource_name)

    def test_get_resource_types_returns_correct(self):
        expected = set(pss.RESOURCE_TYPE_MAP.keys()).union({self.resource_type_name})
        add_resource_type(self.resource_type_name)
        actual = set(get_resource_types())
        self.assertSetEqual(expected, actual)

    def test_get_resources_returns_correct(self):
        expected = set(pss.RESOURCE_MAP.keys()).union({self.resource_name})
        add_resource(self.resource_name, lambda: set(), 'http')
        actual = set(get_resources())
        self.assertSetEqual(expected, actual)


if __name__ == '__main__':
    unittest.main()
    cwd = os.getcwd()
elif __name__ == 'test_scrapers':
    cwd = os.getcwd()
elif __name__ == 'tests.test_scrapers':
    cwd = os.path.join(os.getcwd(), 'tests')
