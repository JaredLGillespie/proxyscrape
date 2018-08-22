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


import time
from threading import Thread
import unittest
from unittest.mock import Mock

# TODO: Change these to not be *
from proxyscrape import *
from proxyscrape.errors import *
import proxyscrape.proxyscrape as ps
from proxyscrape.scrapers import Proxy


RESOURCE_MAP_COPY = ps.RESOURCE_MAP.copy()
RESOURCE_TYPE_MAP_COPY = {k: v.copy() for k, v in ps.RESOURCE_TYPE_MAP.items()}


def hold_lock(lock, hold_time, func):
    with lock:
        time.sleep(hold_time)
        func()


class TestProxyScrape(unittest.TestCase):
    def setUp(self):
        # Revert constants to defaults before each test
        ps.COLLECTORS.clear()
        ps.RESOURCE_MAP = RESOURCE_MAP_COPY.copy()
        ps.RESOURCE_TYPE_MAP = {k: v.copy() for k, v in RESOURCE_TYPE_MAP_COPY.items()}

    def test_add_resource_exception_if_duplicate(self):
        add_resource('my-resource', lambda: set(), 'http')

        with self.assertRaises(ResourceAlreadyDefinedError):
            add_resource('my-resource', lambda: set(), 'http')

    def test_add_resource_exception_if_invalid_resource_type(self):
        with self.assertRaises(InvalidResourceTypeError):
            add_resource('my-resource', lambda: set(), 'invalid')

    def test_add_resource_exception_if_duplicate_lock_check(self):
        def func(): ps.RESOURCE_MAP['my-resource'] = {}
        t = Thread(target=hold_lock, args=(ps._resource_lock, 0.01, func))
        t.start()

        with self.assertRaises(ResourceAlreadyDefinedError):
            add_resource('my-resource', lambda: set(), 'http')

    def test_add_resource_single_resource_type(self):
        add_resource('my-resource', lambda: set(), 'http')

        self.assertIn('my-resource', ps.RESOURCE_MAP)
        self.assertIn('my-resource', ps.RESOURCE_TYPE_MAP['http'])

    def test_add_resource_multiple_resource_types(self):
        add_resource('my-resource', lambda: set(), ['http', 'socks4'])

        self.assertIn('my-resource', ps.RESOURCE_MAP)
        self.assertIn('my-resource', ps.RESOURCE_TYPE_MAP['http'])
        self.assertIn('my-resource', ps.RESOURCE_TYPE_MAP['socks4'])

    def test_add_resource_none_resource_types(self):
        add_resource('my-resource', lambda: set(), None)
        self.assertIn('my-resource', ps.RESOURCE_MAP)

    def test_add_resource_type_exception_if_duplicate(self):
        add_resource_type('my-resource-type')

        with self.assertRaises(ResourceTypeAlreadyDefinedError):
            add_resource_type('my-resource-type')

    def test_add_resource_type_exception_if_duplicate_lock_check(self):
        def func(): ps.RESOURCE_TYPE_MAP['my-resource-type'] = set()
        t = Thread(target=hold_lock, args=(ps._resource_type_lock, 0.01, func))
        t.start()

        with self.assertRaises(ResourceTypeAlreadyDefinedError):
            add_resource_type('my-resource-type')

    def test_add_resource_type_adds_if_new(self):
        add_resource_type('my-resource-type')

    def test_create_collector_exception_if_duplicate(self):
        create_collector('my-collector', 'http')

        with self.assertRaises(CollectorAlreadyDefinedError):
            create_collector('my-collector', 'socks4')

    def test_create_collection_exception_if_duplicate_lock_check(self):
        def func(): ps.COLLECTORS['my-collector'] = object()
        t = Thread(target=hold_lock, args=(ps._collector_lock, 0.01, func))
        t.start()

        with self.assertRaises(CollectorAlreadyDefinedError):
            create_collector('my-collector', 'http')

    def test_create_collector_creates_if_new(self):
        collector = create_collector('my-collector', 'http')
        self.assertIsNotNone(collector)

    def test_get_collector_exception_if_undefined(self):
        with self.assertRaises(CollectorNotFoundError):
            get_collector('undefined')

    def test_get_collector_returns_correct_collector(self):
        expected = object()
        ps.COLLECTORS['my-collector'] = expected
        actual = get_collector('my-collector')
        self.assertEqual(expected, actual)

    def test_get_resource_types_returns_correct(self):
        expected = set(ps.RESOURCE_TYPE_MAP.keys()).union({'my-resource-type'})
        add_resource_type('my-resource-type')
        actual = set(get_resource_types())
        self.assertSetEqual(expected, actual)

    def test_get_resources_returns_correct(self):
        expected = set(ps.RESOURCE_MAP.keys()).union({'my-resource'})
        add_resource('my-resource', lambda: set(), 'http')
        actual = set(get_resources())
        self.assertSetEqual(expected, actual)


class TestCollector(unittest.TestCase):
    def test_exception_if_no_resource_or_resource_type(self):
        with self.assertRaises(InvalidResourceError):
            ps.Collector(None, 10, None)

    def test_exception_if_invalid_resource_type(self):
        with self.assertRaises(InvalidResourceTypeError):
            ps.Collector(object(), 10, None)

    def test_exception_if_invalid_resource_type_if_multiple(self):
        with self.assertRaises(InvalidResourceTypeError):
            ps.Collector(('http', object()), 10, None)

    def test_exception_if_invalid_resources(self):
        with self.assertRaises(InvalidResourceError):
            ps.Collector('http', 10, object())

    def test_initializes_with_single_resource_types(self):
        collector = ps.Collector('http', 10, None)
        self.assertIsNotNone(collector)

    def test_initializes_with_multiple_resource_types(self):
        collector = ps.Collector(('socks4', 'socks5'), 10, None)
        self.assertIsNotNone(collector)

    def test_initializes_with_single_resource(self):
        collector = ps.Collector(None, 10, 'us-proxy')
        self.assertIsNotNone(collector)

    def test_initializes_with_multiple_resources(self):
        collector = ps.Collector(None, 10, ('uk-proxy', 'us-proxy'))
        self.assertIsNotNone(collector)

    def test_apply_filter_ignores_if_none(self):
        collector = ps.Collector('http', 10, None)
        expected = collector._filter_opts

        collector.apply_filter(None)
        actual = collector._filter_opts

        self.assertEqual(expected, actual)

    def test_apply_filter_exception_if_not_dict(self):
        with self.assertRaises(InvalidFilterOptionError):
            collector = ps.Collector('http', 10, None)
            collector.apply_filter(object())

    def test_apply_filter_exception_if_filter_invalid_keys(self):
        with self.assertRaises(InvalidFilterOptionError):
            collector = ps.Collector('http', 10, None)
            collector.apply_filter({'bad-key': 'bad'})

    def test_apply_filter_adds_filter_single(self):
        collector = ps.Collector('http', 10, None)
        collector.apply_filter({'type': 'https'})

    def test_apply_filter_adds_filter_multiple(self):
        collector = ps.Collector('http', 10, None)
        expected = collector._filter_opts
        expected['type'].update({'socks4', 'socks5'})

        collector.apply_filter({'type': {'socks4', 'socks5'}})
        actual = collector._filter_opts

        self.assertEqual(expected['type'], actual['type'])

    def test_apply_filter_adds_filter_different_keys(self):
        collector = ps.Collector('http', 10, None)
        expected = collector._filter_opts
        expected['code'] = {'uk', 'us'}

        collector.apply_filter({'code': {'uk', 'us'}})
        actual = collector._filter_opts

        self.assertEqual(expected['type'], actual['type'])
        self.assertEqual(expected['code'], actual['code'])

    def test_blacklist_proxy_single(self):
        collector = ps.Collector('http', 10, None)
        proxy = Proxy('host', 'port', 'code', 'country', 'anonymous', 'type', 'source')
        collector.blacklist_proxy(proxy)

        self.assertEqual(proxy, collector._blacklist.pop())

    def test_blacklist_proxy_multiple(self):
        collector = ps.Collector('http', 10, None)
        proxies = {
            Proxy('host1', 'port', 'code', 'country', 'anonymous', 'type', 'source'),
            Proxy('host2', 'port', 'code', 'country', 'anonymous', 'type', 'source')
        }

        collector.blacklist_proxy(proxies)

        for proxy in proxies:
            self.assertIn(proxy, collector._blacklist)

    def test_clear_blacklist_clears_correctly(self):
        collector = ps.Collector('http', 10, None)
        proxy = Proxy('host', 'port', 'code', 'country', 'anonymous', 'type', 'source')

        collector.blacklist_proxy(proxy)
        collector.clear_blacklist()

        self.assertSetEqual(set(), collector._blacklist)

    def test_clear_filter_clears_if_no_resource_types(self):
        collector = ps.Collector(None, 10, 'us-proxy')
        collector.apply_filter({'type': 'https'})
        collector.clear_filter()

        self.assertDictEqual({}, collector._filter_opts)

    def test_clear_filter_clears_to_default(self):
        collector = ps.Collector('http', 10, None)
        collector.apply_filter({'type': 'https'})
        collector.clear_filter()

        self.assertSetEqual({'http'}, collector._filter_opts['type'])

    def test_get_proxy_no_filter(self):
        proxy = Proxy('host', 'port', 'code', 'country', 'anonymous', 'type', 'source')
        proxies = {proxy, }

        store_mock = Mock()
        store_mock.return_value = store_mock  # Ensure same instance when initialized
        store_mock.get_proxy.return_value = proxy

        proxy_resource_mock = Mock()
        proxy_resource_mock.return_value = proxy_resource_mock  # Ensure same instance when initialized
        proxy_resource_mock.refresh.return_value = True, proxies

        ps.Store = store_mock
        ps.ProxyResource = proxy_resource_mock

        collector = ps.Collector('http', 10, None)
        actual = collector.get_proxy()

        for _, attrs in collector._resource_map.items():
            store_mock.update_store.assert_called_with(attrs['id'], proxies)

        store_mock.get_proxy.assert_called_once_with({'type': {'http', }}, collector._blacklist)
        self.assertEqual(proxy, actual)

    def test_get_proxy_with_filter(self):
        proxy = Proxy('host', 'port', 'code', 'country', 'anonymous', 'type', 'source')
        proxies = {proxy, }

        store_mock = Mock()
        store_mock.return_value = store_mock  # Ensure same instance when initialized
        store_mock.get_proxy.return_value = proxy

        proxy_resource_mock = Mock()
        proxy_resource_mock.return_value = proxy_resource_mock  # Ensure same instance when initialized
        proxy_resource_mock.refresh.return_value = True, proxies

        ps.Store = store_mock
        ps.ProxyResource = proxy_resource_mock

        collector = ps.Collector('http', 10, None)
        actual = collector.get_proxy({'code': 'us'})

        for _, attrs in collector._resource_map.items():
            store_mock.update_store.assert_called_with(attrs['id'], proxies)

        store_mock.get_proxy.assert_called_once_with({'type': {'http', }, 'code': {'us', }}, collector._blacklist)
        self.assertEqual(proxy, actual)

    def test_get_proxy_doesnt_update_store_if_not_refreshed(self):
        store_mock = Mock()
        store_mock.return_value = store_mock  # Ensure same instance when initialized
        store_mock.get_proxy.return_value = None

        proxy_resource_mock = Mock()
        proxy_resource_mock.return_value = proxy_resource_mock  # Ensure same instance when initialized
        proxy_resource_mock.refresh.return_value = False, None

        ps.Store = store_mock
        ps.ProxyResource = proxy_resource_mock

        collector = ps.Collector('http', 10, None)
        actual = collector.get_proxy()

        store_mock.update_store.assert_not_called()
        store_mock.get_proxy.assert_called_once_with({'type': {'http', }}, collector._blacklist)
        self.assertIsNone(actual)

    def test_remove_proxy_does_nothing_if_none(self):
        store_mock = Mock()
        store_mock.return_value = store_mock  # Ensure same instance when initialized
        store_mock.get_proxy.return_value = None
        ps.Store = store_mock

        collector = ps.Collector('http', 10, None)
        collector.remove_proxy(None)

        store_mock.remove_proxy.assert_not_called()

    def test_remove_proxy_exception_if_invalid_resource_type(self):
        proxy = Proxy('host', 'port', 'code', 'country', 'anonymous', 'type', 'invalid-source')
        collector = ps.Collector('http', 10, None)

        with self.assertRaises(InvalidResourceTypeError):
            collector.remove_proxy(proxy)

    def test_remove_proxy_single(self):
        store_mock = Mock()
        store_mock.return_value = store_mock  # Ensure same instance when initialized
        store_mock.get_proxy.return_value = None
        ps.Store = store_mock

        proxy = Proxy('host', 'port', 'code', 'country', 'anonymous', 'type', 'anonymous-proxy')

        collector = ps.Collector('http', 10, None)
        collector.remove_proxy(proxy)

        id = collector._resource_map['anonymous-proxy']['id']
        store_mock.remove_proxy.assert_called_with(id, proxy)

    def test_remove_proxy_multiple(self):
        store_mock = Mock()
        store_mock.return_value = store_mock  # Ensure same instance when initialized
        store_mock.get_proxy.return_value = None
        ps.Store = store_mock

        proxy1 = Proxy('host1', 'port', 'code', 'country', 'anonymous', 'type', 'anonymous-proxy')
        proxy2 = Proxy('host2', 'port', 'code', 'country', 'anonymous', 'type', 'us-proxy')
        proxies = {proxy1, proxy2}

        collector = ps.Collector('http', 10, None)
        collector.remove_proxy(proxies)

        id = collector._resource_map['anonymous-proxy']['id']
        store_mock.remove_proxy.assert_any_call(id, proxy1)

        id = collector._resource_map['us-proxy']['id']
        store_mock.remove_proxy.assert_any_call(id, proxy2)

    def test_refresh_proxies_update_store_if_refreshed(self):
        proxy = Proxy('host', 'port', 'code', 'country', 'anonymous', 'type', 'source')
        proxies = {proxy, }

        store_mock = Mock()
        store_mock.return_value = store_mock  # Ensure same instance when initialized
        store_mock.get_proxy.return_value = None

        proxy_resource_mock = Mock()
        proxy_resource_mock.return_value = proxy_resource_mock  # Ensure same instance when initialized
        proxy_resource_mock.refresh.return_value = True, proxies

        ps.Store = store_mock
        ps.ProxyResource = proxy_resource_mock

        collector = ps.Collector('http', 10, None)
        collector.refresh_proxies()

        proxy_resource_mock.refresh.assert_called_with(True)

        for _, attrs in collector._resource_map.items():
            store_mock.update_store.assert_called_with(attrs['id'], proxies)

    def test_refresh_proxies_doesnt_update_store_if_not_refreshed(self):
        store_mock = Mock()
        store_mock.return_value = store_mock  # Ensure same instance when initialized
        store_mock.get_proxy.return_value = None

        proxy_resource_mock = Mock()
        proxy_resource_mock.return_value = proxy_resource_mock  # Ensure same instance when initialized
        proxy_resource_mock.refresh.return_value = False, None

        ps.Store = store_mock
        ps.ProxyResource = proxy_resource_mock

        collector = ps.Collector('http', 10, None)
        collector.refresh_proxies()

        proxy_resource_mock.refresh.assert_called_with(True)
        store_mock.update_store.assert_not_called()

    def test_refresh_proxies_with_no_force(self):
        proxy = Proxy('host', 'port', 'code', 'country', 'anonymous', 'type', 'source')
        proxies = {proxy, }

        store_mock = Mock()
        store_mock.return_value = store_mock  # Ensure same instance when initialized
        store_mock.get_proxy.return_value = None

        proxy_resource_mock = Mock()
        proxy_resource_mock.return_value = proxy_resource_mock  # Ensure same instance when initialized
        proxy_resource_mock.refresh.return_value = True, proxies

        ps.Store = store_mock
        ps.ProxyResource = proxy_resource_mock

        collector = ps.Collector('http', 10, None)
        collector.refresh_proxies(False)

        proxy_resource_mock.refresh.assert_called_with(False)

        for _, attrs in collector._resource_map.items():
            store_mock.update_store.assert_called_with(attrs['id'], proxies)


if __name__ == '__main__':
    unittest.main()
