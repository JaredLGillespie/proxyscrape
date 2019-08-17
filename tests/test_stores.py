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
from proxyscrape.scrapers import Proxy
from proxyscrape.stores import Store


class TestStores(unittest.TestCase):
    def test_add_store_returns_id(self):
        store = Store()
        id = store.add_store()
        self.assertIsNotNone(id)

    def test_get_proxy_returns_empty_if_no_stores(self):
        store = Store()
        proxy = store.get_proxy()
        self.assertIsNone(proxy)

    def test_get_proxy_returns_empty_if_empty(self):
        store = Store()
        store.add_store()
        proxy = store.get_proxy()
        self.assertIsNone(proxy)

    def test_get_proxy_returns_empty_if_filtered(self):
        store = Store()
        id = store.add_store()
        proxy = Proxy('host', 'source', 'us', 'united states', True, 'type', 'source')

        store.update_store(id, {proxy, })
        actual = store.get_proxy(filter_opts={'code': {'uk', }})

        self.assertIsNone(actual)

    def test_get_proxy_returns_proxy_if_not_filtered(self):
        store = Store()
        id = store.add_store()
        proxy = Proxy('host', 'source', 'us', 'united states', True, 'type', 'source')

        store.update_store(id, {proxy, })
        actual = store.get_proxy(filter_opts={'code': {'us', }})

        self.assertEqual(actual, proxy)

    def test_get_proxy_returns_empty_if_blacklisted(self):
        store = Store()
        id = store.add_store()
        proxy = Proxy('host', 'source', 'us', 'united states', True, 'type', 'source')

        store.update_store(id, {proxy, })
        actual = store.get_proxy(blacklist={(proxy[0], proxy[1]), })

        self.assertIsNone(actual)

    def test_get_proxy_returns_empty_if_filtered_and_blacklisted(self):
        store = Store()
        id = store.add_store()
        proxy = Proxy('host', 'source', 'us', 'united states', True, 'type', 'source')

        store.update_store(id, {proxy, })
        actual = store.get_proxy(filter_opts={'country': {'uk', }},
                                 blacklist={(proxy[0], proxy[1]), })

        self.assertIsNone(actual)

    def test_get_proxy_returns_empty_if_not_filtered_and_blacklisted(self):
        store = Store()
        id = store.add_store()
        proxy = Proxy('host', 'source', 'us', 'united states', True, 'type', 'source')

        store.update_store(id, {proxy, })
        actual = store.get_proxy(filter_opts={'code': {'us', }},
                                 blacklist={(proxy[0], proxy[1]), })

        self.assertIsNone(actual)

    def test_get_proxy_returns_proxy_if_any(self):
        store = Store()
        id = store.add_store()
        expected = Proxy('host', 'source', 'us', 'united states', True, 'type', 'source')

        store.update_store(id, {expected, })
        actual = store.get_proxy()

        self.assertEqual(actual, expected)

    def test_get_proxies_returns_empty_if_no_stores(self):
        store = Store()
        proxies = store.get_proxies()
        self.assertIsNone(proxies)

    def test_get_proxies_returns_empty_if_empty(self):
        store = Store()
        store.add_store()
        proxies = store.get_proxies()
        self.assertIsNone(proxies)

    def test_get_proxies_returns_empty_if_filtered(self):
        store = Store()
        id = store.add_store()
        proxy = Proxy('host', 'source', 'us', 'united states', True, 'type', 'source')

        store.update_store(id, {proxy, })
        actual = store.get_proxies(filter_opts={'code': {'uk', }})

        self.assertIsNone(actual)

    def test_get_proxies_returns_proxies_if_not_filtered(self):
        store = Store()
        id = store.add_store()
        proxy = Proxy('host', 'source', 'us', 'united states', True, 'type', 'source')

        store.update_store(id, {proxy, })
        actual = store.get_proxies(filter_opts={'code': {'us', }})

        self.assertEqual(actual[0], proxy)

    def test_get_proxies_returns_empty_if_blacklisted(self):
        store = Store()
        id = store.add_store()
        proxy = Proxy('host', 'source', 'us', 'united states', True, 'type', 'source')

        store.update_store(id, {proxy, })
        actual = store.get_proxies(blacklist={(proxy[0], proxy[1]), })

        self.assertIsNone(actual)

    def test_get_proxies_returns_empty_if_filtered_and_blacklisted(self):
        store = Store()
        id = store.add_store()
        proxy = Proxy('host', 'source', 'us', 'united states', True, 'type', 'source')

        store.update_store(id, {proxy, })
        actual = store.get_proxies(filter_opts={'country': {'uk', }},
                                   blacklist={(proxy[0], proxy[1]), })

        self.assertIsNone(actual)

    def test_get_proxies_returns_empty_if_not_filtered_and_blacklisted(self):
        store = Store()
        id = store.add_store()
        proxy = Proxy('host', 'source', 'us', 'united states', True, 'type', 'source')

        store.update_store(id, {proxy, })
        actual = store.get_proxies(filter_opts={'code': {'us', }},
                                   blacklist={(proxy[0], proxy[1]), })

        self.assertIsNone(actual)

    def test_get_proxies_returns_proxies_if_any(self):
        store = Store()
        id = store.add_store()
        expected = Proxy('host', 'source', 'us', 'united states', True, 'type', 'source')

        store.update_store(id, {expected, })
        actual = store.get_proxies()

        self.assertEqual(actual[0], expected)

    def test_remove_proxy_removes_from_set(self):
        store = Store()
        id = store.add_store()
        proxy = Proxy('host', 'source', 'us', 'united states', True, 'type', 'source')

        store.update_store(id, {proxy, })
        actual1 = store.get_proxy()

        store.remove_proxy(id, proxy)
        actual2 = store.get_proxy()

        self.assertEqual(actual1, proxy)
        self.assertIsNone(actual2)

    def test_remove_proxy_invalid_id_does_nothing(self):
        store = Store()
        proxy = Proxy('host', 'source', 'us', 'united states', True, 'type', 'source')
        store.remove_proxy(1, proxy)

        proxy = store.get_proxy()
        self.assertIsNone(proxy)

    def test_update_store_clears_if_none(self):
        store = Store()
        id = store.add_store()
        proxy = Proxy('host', 'source', 'us', 'united states', True, 'type', 'source')

        store.update_store(id, {proxy, })
        actual1 = store.get_proxy()

        store.update_store(id, None)
        actual2 = store.get_proxy()

        self.assertEqual(proxy, actual1)
        self.assertIsNone(actual2)

    def test_update_store_updates_proxies(self):
        store = Store()
        id = store.add_store()
        proxy = Proxy('host', 'source', 'us', 'united states', True, 'type', 'source')

        store.update_store(id, {proxy, })
        actual = store.get_proxy()

        self.assertEqual(proxy, actual)

    def test_update_store_invalid_id_does_nothing(self):
        store = Store()
        proxy = Proxy('host', 'source', 'us', 'united states', True, 'type', 'source')
        store.update_store(1, {proxy, })

        proxy = store.get_proxy()
        self.assertIsNone(proxy)


if __name__ == '__main__':
    unittest.main()
    cwd = os.getcwd()
elif __name__ == 'test_stores':
    cwd = os.getcwd()
elif __name__ == 'tests.test_stores':
    cwd = os.path.join(os.getcwd(), 'tests')
