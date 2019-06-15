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
import unittest
try:
    from unittest.mock import Mock, patch
except ImportError:
    from mock import Mock, patch


from proxyscrape.integration import get_proxyscrape_resource
from proxyscrape.scrapers import (
    ProxyResource
)
import proxyscrape.scrapers as pss
from proxyscrape.shared import Proxy


RESOURCE_MAP_COPY = pss.RESOURCE_MAP.copy()


class TestIntegrationProxyScrape(unittest.TestCase):
    def setUp(self):
        self.requests_patcher = patch('proxyscrape.shared.requests')
        self.requests = self.requests_patcher.start()

        # Revert constants to defaults before each test
        pss.RESOURCE_MAP = RESOURCE_MAP_COPY.copy()

    def test_get_proxyscrape_resource_success(self):
        resource_name = get_proxyscrape_resource()
        self.assertIn(resource_name, pss.RESOURCE_MAP)

    def test_get_proxyscrape_resource_duplicate(self):
        resource_name1 = get_proxyscrape_resource()
        resource_name2 = get_proxyscrape_resource()
        self.assertEqual(resource_name1, resource_name2)
        self.assertIn(resource_name2, pss.RESOURCE_MAP)

    def test_get_proxyscrape_resource_invalid_proxytype(self):
        with self.assertRaises(ValueError):
            get_proxyscrape_resource(proxytype='')

    def test_get_proxyscrape_resource_invalid_timeout(self):
        with self.assertRaises(ValueError):
            get_proxyscrape_resource(timeout=0)

    def test_get_proxyscrape_resource_invalid_ssl(self):
        with self.assertRaises(ValueError):
            get_proxyscrape_resource(ssl='')

    def test_get_proxyscrape_resource_invalid_anonymity(self):
        with self.assertRaises(ValueError):
            get_proxyscrape_resource(anonymity='')

    def test_get_proxyscrape_resource_invalid_country(self):
        with self.assertRaises(ValueError):
            get_proxyscrape_resource(country='')

    def test_proxyscrape_success(self):
        with open(os.path.join(cwd, 'mock_pages', 'proxyscrape.txt'), 'r') as html:
            response = Mock()
            response.text = html.read()
            response.ok = True
            self.requests.get = lambda url: response

            resource_name = get_proxyscrape_resource()

            expected = {
                Proxy('179.124.59.232', '53281', None, None, False, None, resource_name),
                Proxy('200.107.59.98', '8080', None, None, False, None, resource_name),
                Proxy('217.172.244.7', '8080', None, None, False, None, resource_name)
            }

            func = pss.RESOURCE_MAP[resource_name]
            pr = ProxyResource(func, 10)

            _, proxies = pr.refresh()

            for proxy in proxies:
                self.assertIn(proxy, expected)

    def test_proxyscrape_not_ok(self):
        response = Mock()
        response.ok = False
        self.requests.get = lambda url: response

        resource_name = get_proxyscrape_resource()
        func = pss.RESOURCE_MAP[resource_name]
        pr = ProxyResource(func, 10)

        refreshed, proxies = pr.refresh()

        self.assertEqual(False, refreshed)
        self.assertIsNone(proxies)

    def test_us_proxies_invalid_html(self):
        with open(os.path.join(cwd, 'mock_pages', 'empty.html'), 'r') as html:
            response = Mock()
            response.text = html.read()
            response.ok = True
            self.requests.get = lambda url: response

            resource_name = get_proxyscrape_resource()
            func = pss.RESOURCE_MAP[resource_name]
            pr = ProxyResource(func, 10)

            refreshed, proxies = pr.refresh()

            self.assertEqual(False, refreshed)
            self.assertIsNone(proxies)


if __name__ == '__main__':
    unittest.main()
    cwd = os.getcwd()
elif __name__ == 'test_integration':
    cwd = os.getcwd()
elif __name__ == 'tests.test_integration':
    cwd = os.path.join(os.getcwd(), 'tests')
