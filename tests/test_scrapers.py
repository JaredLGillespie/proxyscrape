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
import time
import unittest
from unittest.mock import Mock, patch
from proxyscrape.scrapers import Proxy, ProxyResource, RESOURCE_MAP


class TestProxyResource(unittest.TestCase):
    def test_refreshes_if_expired(self):
        expected = [Proxy('host', 'port', 'code', 'country', 'anonymous', 'type', 'source')]
        call_count = 0

        def func():
            nonlocal call_count
            call_count += 1
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
        call_count = 0

        def func():
            nonlocal call_count
            call_count += 1
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
        call_count = 0

        def func():
            nonlocal call_count
            call_count += 1
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
        call_count = 0

        def func():
            nonlocal call_count
            call_count += 1
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
        self.requests_patcher = patch('proxyscrape.scrapers.requests')
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


# class TestScrapers2(unittest.TestCase):
#     def test_anonymous_proxies(self):
#         expected = {
#             Proxy('179.124.59.232', '53281', 'br', 'brazil', True, 'https', 'anonymous-proxy'),
#             Proxy('200.107.59.98', '8080', 'ua', 'ukraine', True, 'http', 'anonymous-proxy'),
#             Proxy('217.172.244.7', '8080', 'ru', 'russian federation', True, 'http', 'anonymous-proxy')
#         }
#
#         func = RESOURCE_MAP['anonymous-proxy']
#         pr = ProxyResource(func, 10)
#
#         _, proxies = pr.refresh()
#
#         for proxy in proxies:
#             self.assertIn(proxy, expected)


if __name__ == '__main__':
    unittest.main()
    cwd = os.getcwd()
elif __name__ == 'test_scrapers':
    cwd = os.getcwd()
elif __name__ == 'tests.test_scrapers':
    cwd = os.path.join(os.getcwd(), 'tests')
