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

from threading import Lock
import random
import uuid


FILTER_OPTIONS = {
    'code',  # us, ca, ...
    'country',  # united states, canada, ...
    'anonymous',  # True, False
    'type',  # http, https, socks4, socks5, ...
}


class Store:
    """An internal store for retrieved proxies.

    Each `ProxyResource` is mapped to an internal 'store' within this class.
    """
    def __init__(self):
        # Maps a uuid to a store
        self._stores = {}
        self._lock = Lock()

    @staticmethod
    def _filter_proxies(proxies, filter_opts=None, blacklist=None):
        if not filter_opts:
            if not blacklist:
                return proxies
            return [p for p in proxies if (p[0], p[1]) not in blacklist]

        def filter_func(proxy):
            for attr, values in filter_opts.items():
                if getattr(proxy, attr, None) not in values:
                    return False

            if blacklist and (proxy[0], proxy[1]) in blacklist:
                return False

            return True

        return filter(filter_func, proxies)

    def add_store(self):
        """Adds a new internal store for use by a single `ProxyResource`.

        :return:
            The unique identifier assigned to the store.
        :rtype: uuid
        """
        id = uuid.uuid4()
        self._stores[id] = set()
        return id

    def get_proxy(self, filter_opts=None, blacklist=None):
        """Retrieves a single proxy.

        :param filter_opts:
            (optional) Options to filter the proxies by.
        :param blacklist:
            (optional) Specific proxies to not retrieve.
        :type filter_opts: dict or None
        :type blacklist: set
        :return:
            A single proxy matching the given filters.
        :rtype: Proxy or None
        """
        filtered_proxies = self.get_proxies(filter_opts=filter_opts, blacklist=blacklist)

        if filtered_proxies is None:
            return None

        return random.sample(filtered_proxies, 1)[0]

    def get_proxies(self, filter_opts=None, blacklist=None):
        """Retrieves all proxies.

        :param filter_opts:
            (optional) Options to filter the proxies by.
        :param blacklist:
            (optional) Specific proxies to not retrieve.
        :type filter_opts: dict or None
        :type blacklist: set
        :return:
            All proxies matching the given filters.
        :rtype: List of Proxy or None
        """
        proxies = set()
        for store in self._stores.values():
            proxies.update(store)

        # No proxies found in any store
        if not proxies:
            return None

        filtered_proxies = set(self._filter_proxies(proxies, filter_opts, blacklist))

        # No proxies found based on filter
        if not filtered_proxies:
            return None

        return list(filtered_proxies)

    def remove_proxy(self, id, proxy):
        """Removes a proxy from the internal store.

        :param id:
            The unique identifier of the store.
        :param proxy:
            The proxy to remove.
        :type id: uuid
        :type proxy: Proxy
        """
        if id not in self._stores:
            return

        self._stores[id].difference_update({proxy, })

    def update_store(self, id, proxies):
        """Updates the store with the given proxies.

        This clears the store of pre-existing proxies and adds the new ones.

        :param id:
            The unique identifier of the store.
        :param proxies:
            The proxies to add to the store.
        :type id: uuid
        :type proxies: set
        """
        if id not in self._stores:
            return

        store = self._stores[id]

        with self._lock:
            store.clear()

            if proxies:
                store.update(proxies)
