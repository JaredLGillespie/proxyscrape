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
    from unittest.mock import Mock
except ImportError:
    from mock import Mock

from proxyscrape.errors import (
     CollectorAlreadyDefinedError,
     CollectorNotFoundError,
     InvalidFilterOptionError,
     InvalidResourceError,
     InvalidResourceTypeError
)
import proxyscrape.proxyscrape as ps
from proxyscrape.proxyscrape import (
    create_collector,
    get_collector
)
from proxyscrape.shared import Proxy


def hold_lock(lock, hold_time, func):
    time.sleep(hold_time)
    func()
    lock.release()


def get_random_collector_name(self):
    return self._testMethodName + '-collector'


class TestProxyScrape(unittest.TestCase):
    def setUp(self):
        # Revert constants to defaults before each test
        ps.COLLECTORS.clear()
        self.collector_name = get_random_collector_name(self)

    def test_create_collector_exception_if_duplicate(self):
        create_collector(self.collector_name, 'http')

        with self.assertRaises(CollectorAlreadyDefinedError):
            create_collector(self.collector_name, 'socks4')

    def test_create_collection_exception_if_duplicate_lock_check(self):
        # Intermittent failure in Python 2.7
        if sys.version_info.major < 3:
            return

        def func(): ps.COLLECTORS[self.collector_name] = object()
        ps._collector_lock.acquire()
        t = Thread(target=hold_lock, args=(ps._collector_lock, 0.1, func))
        t.start()

        with self.assertRaises(CollectorAlreadyDefinedError):
            create_collector(self.collector_name, 'http')

        t.join()

    def test_create_collector_creates_if_new(self):
        collector = create_collector(self.collector_name, 'http')
        self.assertIsNotNone(collector)

    def test_get_collector_exception_if_undefined(self):
        with self.assertRaises(CollectorNotFoundError):
            get_collector('undefined')

    def test_get_collector_returns_correct_collector(self):
        expected = object()
        ps.COLLECTORS[self.collector_name] = expected
        actual = get_collector(self.collector_name)
        self.assertEqual(expected, actual)


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
        expected['type'] = {'socks4', 'socks5'}

        collector.apply_filter({'type': {'socks4', 'socks5'}})
        actual = collector._filter_opts

        self.assertEqual(len(expected), len(actual))
        self.assertEqual(expected['type'], actual['type'])

    def test_apply_filter_adds_filter_different_keys(self):
        collector = ps.Collector('http', 10, None)
        expected = collector._filter_opts
        expected['code'] = {'uk', 'us'}

        collector.apply_filter({'code': {'uk', 'us'}})
        actual = collector._filter_opts

        self.assertEqual(len(expected), len(actual))
        self.assertEqual(expected['code'], actual['code'])

    def test_blacklist_proxy_single(self):
        collector = ps.Collector('http', 10, None)
        proxy = Proxy('host', 'port', 'code', 'country', 'anonymous', 'type', 'source')
        collector.blacklist_proxy(proxy)

        self.assertEqual((proxy[0], proxy[1]), collector._blacklist.pop())

    def test_blacklist_proxy_multiple(self):
        collector = ps.Collector('http', 10, None)
        proxies = {
            Proxy('host1', 'port', 'code', 'country', 'anonymous', 'type', 'source'),
            Proxy('host2', 'port', 'code', 'country', 'anonymous', 'type', 'source')
        }

        collector.blacklist_proxy(proxies)

        for proxy in proxies:
            self.assertIn((proxy[0], proxy[1]), collector._blacklist)

    def test_blacklist_proxy_exception_if_invalid_parameters(self):
        collector = ps.Collector('http', 10, None)
        with self.assertRaises(ValueError):
            collector.blacklist_proxy()

    def test_blacklist_proxy_single_with_host_and_port(self):
        collector = ps.Collector('http', 10, None)
        collector.blacklist_proxy(host='host', port='port')

        self.assertEqual(('host', 'port'), collector._blacklist.pop())

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

        store_mock.get_proxy.assert_called_once_with({}, collector._blacklist)
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

        store_mock.get_proxy.assert_called_once_with({'code': {'us', }}, collector._blacklist)
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
        store_mock.get_proxy.assert_called_once_with({}, collector._blacklist)
        self.assertIsNone(actual)

    def test_get_proxies_no_filter(self):
        proxy1 = Proxy('host1', 'port1', 'code', 'country', 'anonymous', 'type', 'source')
        proxy2 = Proxy('host2', 'por2', 'code', 'country', 'anonymous', 'type', 'source')
        proxies = {proxy1, proxy2}

        store_mock = Mock()
        store_mock.return_value = store_mock  # Ensure same instance when initialized
        store_mock.get_proxies.return_value = [proxy1, proxy2]

        proxy_resource_mock = Mock()
        proxy_resource_mock.return_value = proxy_resource_mock  # Ensure same instance when initialized
        proxy_resource_mock.refresh.return_value = True, proxies

        ps.Store = store_mock
        ps.ProxyResource = proxy_resource_mock

        collector = ps.Collector('http', 10, None)
        actual = collector.get_proxies()

        for _, attrs in collector._resource_map.items():
            store_mock.update_store.assert_called_with(attrs['id'], proxies)

        store_mock.get_proxies.assert_called_once_with({}, collector._blacklist)

        for proxy in proxies:
            self.assertIn(proxy, actual)

    def test_get_proxies_with_filter(self):
        proxy1 = Proxy('host1', 'port1', 'code', 'country', 'anonymous', 'type', 'source')
        proxy2 = Proxy('host2', 'por2', 'code', 'country', 'anonymous', 'type', 'source')
        proxies = {proxy1, proxy2}

        store_mock = Mock()
        store_mock.return_value = store_mock  # Ensure same instance when initialized
        store_mock.get_proxies.return_value = [proxy1, proxy2]

        proxy_resource_mock = Mock()
        proxy_resource_mock.return_value = proxy_resource_mock  # Ensure same instance when initialized
        proxy_resource_mock.refresh.return_value = True, proxies

        ps.Store = store_mock
        ps.ProxyResource = proxy_resource_mock

        collector = ps.Collector('http', 10, None)
        actual = collector.get_proxies({'code': 'us'})

        for _, attrs in collector._resource_map.items():
            store_mock.update_store.assert_called_with(attrs['id'], proxies)

        store_mock.get_proxies.assert_called_once_with({'code': {'us', }}, collector._blacklist)

        for proxy in proxies:
            self.assertIn(proxy, actual)

    def test_get_proxies_doesnt_update_store_if_not_refreshed(self):
        store_mock = Mock()
        store_mock.return_value = store_mock  # Ensure same instance when initialized
        store_mock.get_proxies.return_value = None

        proxy_resource_mock = Mock()
        proxy_resource_mock.return_value = proxy_resource_mock  # Ensure same instance when initialized
        proxy_resource_mock.refresh.return_value = False, None

        ps.Store = store_mock
        ps.ProxyResource = proxy_resource_mock

        collector = ps.Collector('http', 10, None)
        actual = collector.get_proxies()

        store_mock.update_store.assert_not_called()
        store_mock.get_proxies.assert_called_once_with({}, collector._blacklist)
        self.assertIsNone(actual)

    def test_remove_blacklist_single(self):
        collector = ps.Collector('http', 10, None)
        proxy = Proxy('host', 'port', 'code', 'country', 'anonymous', 'type', 'source')
        collector.blacklist_proxy(proxy)
        collector.remove_blacklist(proxy)

        self.assertEqual(0, len(collector._blacklist))

    def test_remove_blacklist_multiple(self):
        collector = ps.Collector('http', 10, None)
        proxies = {
            Proxy('host1', 'port', 'code', 'country', 'anonymous', 'type', 'source'),
            Proxy('host2', 'port', 'code', 'country', 'anonymous', 'type', 'source')
        }

        collector.blacklist_proxy(proxies)
        collector.remove_blacklist(proxies)

        self.assertEqual(0, len(collector._blacklist))

    def test_remove_blacklist_exception_if_invalid_parameters(self):
        collector = ps.Collector('http', 10, None)
        with self.assertRaises(ValueError):
            collector.remove_blacklist()

    def test_remove_blacklist_single_with_host_and_port(self):
        collector = ps.Collector('http', 10, None)
        proxy = Proxy('host', 'port', 'code', 'country', 'anonymous', 'type', 'source')
        collector.blacklist_proxy(proxy)
        collector.remove_blacklist(host='host', port='port')

        self.assertEqual(0, len(collector._blacklist))

    def test_remove_blacklist_removes_correct_proxy(self):
        collector = ps.Collector('http', 10, None)
        proxy1 = Proxy('host1', 'port', 'code', 'country', 'anonymous', 'type', 'source')
        proxy2 = Proxy('host2', 'port', 'code', 'country', 'anonymous', 'type', 'source')
        proxies = {proxy1, proxy2}

        collector.blacklist_proxy(proxies)
        collector.remove_blacklist(proxy1)

        self.assertEqual(1, len(collector._blacklist))
        self.assertIn((proxy2[0], proxy2[1]), collector._blacklist)

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
    cwd = os.getcwd()
elif __name__ == 'test_proxyscrape':
    cwd = os.getcwd()
elif __name__ == 'tests.test_proxyscrape':
    cwd = os.path.join(os.getcwd(), 'tests')
