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

__all__ = ['create_collector', 'get_collector']


from threading import Lock

from .errors import (
    CollectorAlreadyDefinedError,
    CollectorNotFoundError,
    InvalidFilterOptionError,
    InvalidResourceError,
    InvalidResourceTypeError
)
from .scrapers import RESOURCE_MAP, RESOURCE_TYPE_MAP, ProxyResource
from .stores import Store, FILTER_OPTIONS
from .shared import is_iterable


# Module-level references to collectors
COLLECTORS = {}
_collector_lock = Lock()


def create_collector(name, resource_types=None, refresh_interval=3600, resources=None):
    """Creates a new collector to scrape and retrieve proxies.

    Collectors are stored at the module level. A collector should be creates at the start of the application, and can be
    retrieved later on via `proxyscrape.get_collector(...)`

    :param name:
        An identifier for the collector.
    :param resource_types:
        (optional) The resource types to to scrape. Can either be a single or sequence of resource types. Either
        `resource_types` or `resources` should be defined (but not necessarily both).
    :param refresh_interval:
        The amount of time (in seconds) between refreshing the resources. Resources are stored in memory until they are
        refreshed, at which they are flushed and retrieved again.
    :param resources:
        (optional) The resources to scrape. Can either be a single or sequence of resources. Either `resource_types` or
        `resources` should be defined (but not necessarily both).
    :type name: string
    :type resource_types: iterable or string or None
    :type refresh_interval: int
    :type resources: iterable or string or None
    :return:
        The initialized collector.
    :rtype: Collector
    :raises CollectorAlreadyDefinedError:
        If `name` is already a defined collector.
    :raises InvalidResourceError:
        If 'resources' is not a valid resource.
    :raises InvalidResourceTypeError:
        If 'resource_type' is not a valid resource type.
    """
    if name in COLLECTORS:
        raise CollectorAlreadyDefinedError('{} is already defined as a collector'.format(name))

    with _collector_lock:
        # Ensure not added by the time entered lock
        if name in COLLECTORS:
            raise CollectorAlreadyDefinedError('{} is already defined as a collector'.format(name))

        collector = Collector(resource_types, refresh_interval, resources)
        COLLECTORS[name] = collector
        return collector


def get_collector(name):
    """Retrieves a defined collector.

    :param name:
        An identifier for the collector.
    :type name: string
    :return:
        The collector.
    :rtype: Collector
    :raises CollectorNotFoundError:
        If `name` is not a defined collector.
    """
    if name in COLLECTORS:
        return COLLECTORS[name]

    raise CollectorNotFoundError('{} is not a defined collector'.format(name))


class Collector:
    """A proxy collector for retrieving proxies.

    :param resource_types:
        (optional) The resource types to to scrape. Can either be a single or sequence of resource types. Either
        `resource_types` or `resources` should be defined (but not necessarily both).
    :param refresh_interval:
        The amount of time (in seconds) between refreshing the resources. Resources are stored in memory until they are
        refreshed, at which they are flushed and retrieved again.
    :param resources:
        (optional) The resources to scrape. Can either be a single or sequence of resources. Either `resource_types` or
        `resources` should be defined (but not necessarily both).
    :type resource_types: iterable or string or None
    :type refresh_interval: int
    :type resources: iterable or string or None
    :raises InvalidResourceError:
        If 'resources' is not a valid resource.
    :raises InvalidResourceTypeError:
        If 'resource_type' is not a valid resource type.
    """
    def __init__(self, resource_types, refresh_interval, resources):
        self._store = Store()
        self._blacklist = set()

        if resource_types is not None:
            self._resource_types = set(resource_types) if is_iterable(resource_types) else {resource_types, }
            self._validate_resource_types(self._resource_types)
            self._filter_opts = {}
        else:
            self._resource_types = None
            self._filter_opts = {}

        # Input validations
        resources = self._parse_resources(self._resource_types, resources)
        self._validate_resources(resources)

        self._resource_map = self._create_resource_map(resources, refresh_interval)

    def _create_resource_map(self, resources, refresh_interval):
        resource_map = dict()
        for resource in resources:
            id = self._store.add_store()
            func = RESOURCE_MAP[resource]
            resource_map[resource] = {
                'proxy-resource': ProxyResource(func, refresh_interval),
                'id': id
            }

        return resource_map

    def _extend_filter(self, existing_filter_opts, new_filter_opts):
        if not new_filter_opts:
            return existing_filter_opts

        for key, value in new_filter_opts.items():
            if not is_iterable(value):
                value = {value, }
            value = set(value)

            if key in existing_filter_opts:
                existing_filter_opts[key].update(value)
            else:
                existing_filter_opts[key] = value

    def _parse_resources(self, resource_types, resources):
        # Retrieve defaults if none specified
        if resources is None:
            if resource_types is None:
                raise InvalidResourceError('No resource or resource type given')

            res = set()
            for resource_type in resource_types:
                res.update(RESOURCE_TYPE_MAP[resource_type])
            return res

        if is_iterable(resources):
            return set(resources)
        else:
            return {resources, }

    def _refresh_resources(self, force):
        for resource in self._resource_map.values():
            refreshed, proxies = resource['proxy-resource'].refresh(force)

            if refreshed:
                self._store.update_store(resource['id'], proxies)

    def _validate_filter_opts(self, filter_opts):
        if not filter_opts:
            return

        if not isinstance(filter_opts, dict):
            raise InvalidFilterOptionError('{} must be a dictionary'.format(filter_opts))

        for key in filter_opts:
            if key not in FILTER_OPTIONS:
                raise InvalidFilterOptionError('{} is an invalid filter option'.format(key))

    def _validate_resource_types(self, resource_types):
        if set(resource_types).difference(RESOURCE_TYPE_MAP.keys()):
            raise InvalidResourceTypeError(
                '{} defined an invalid resource type'.format(resource_types))

    def _validate_resources(self, resources):
        for resource in resources:
            if resource not in RESOURCE_MAP:
                raise InvalidResourceError('{} is an invalid resource'.format(resource))

    def apply_filter(self, filter_opts):
        """Applies a filter to the collector for retrieving proxies matching specific criteria.

        A filter should defined properties of a proxy that must match for it to be retrievable. Valid properties are:
            - code  (us, ca, ...)
            - country  (united states, canada, ...)
            - anonymous  (True, False)
            - type  (http, https, socks4, socks5, ...)

        Filter_opts should be a dictionary with keys being a valid filter option
        and values either a single string or a collections of strings.

        Filters applied are additive; calling this function multiple times with different filters adds them as a single
        large filter.

        ex. filter_opts = {
            'code': 'us'
        }

        ex. filter_opts = {
            'code': ['us', 'uk']
        }

        :param filter_opts:
            Options to filter proxies retrieved by the collector.
        :type filter_opts: dict
        :raises InvalidFilterOptionError:
            If `filter_opts` is not a dictionary or defines an invalid filter.
        """
        self._validate_filter_opts(filter_opts)
        self._extend_filter(self._filter_opts, filter_opts)

    def blacklist_proxy(self, proxies=None, host=None, port=None):
        """Blacklists a specific a proxy from being retrieved.

        Either a single or sequence of proxies should be given, or a host and port number combination.

        :param proxies:
            (optional) A single or sequence of proxies to blacklist.
        :param host:
            (optional) The host IP of the proxy.
        :param port:
            (optional) The port number of the proxy.
        :type proxies: Proxy or iterable or None
        :type host: str or None
        :type port: str or None
        :raises ValueError:
            If neither proxies nor host and port are given.
        """
        if proxies is None and None in (host, port):
            raise ValueError('Either proxies or host and port should be given')

        if proxies is None:
            proxies = {(host, port), }
        elif not is_iterable(proxies):
            proxies = {(proxies[0], proxies[1]), }
        else:
            proxies = {(p[0], p[1]) for p in proxies}

        self._blacklist.update(proxies)

    def clear_blacklist(self):
        """Clears the blacklist."""
        self._blacklist.clear()

    def clear_filter(self):
        """Clears the filter."""
        if self._resource_types:
            self._filter_opts = {'type': self._resource_types.copy()}
        else:
            self._filter_opts = {}

    def get_proxy(self, filter_opts=None):
        """Retrieves a single proxy.

        A single proxy is retrieved from the internal store. If `refreshed` is True and proxies haven't been retrieved
        within the collector's `refresh_interval`, they are refreshed by clearing the internal store and retrieving new
        proxies.

        :param filter_opts:
            (optional) Options to filter proxies retrieved by collector.
        :type filter_opts: dict or None
        :return:
            The retrieved proxy or None if no proxy found (either because none exist in internal store or none matched
             filter_opts).
        :rtype: Proxy or None
        :raises InvalidFilterOptionError:
            If `filter_opts` is not a dictionary or defines an invalid filter.
        """
        self._validate_filter_opts(filter_opts)

        combined_filter_opts = dict()
        self._extend_filter(combined_filter_opts, self._filter_opts)
        self._extend_filter(combined_filter_opts, filter_opts)

        self._refresh_resources(False)

        return self._store.get_proxy(combined_filter_opts, self._blacklist)

    def get_proxies(self, filter_opts=None):
        """Retrieves proxies.

        All proxies retrieved are from the internal store. If `refreshed` is True and proxies haven't been retrieved
        within the collector's `refresh_interval`, they are refreshed by clearing the internal store and retrieving new
        proxies.

        :param filter_opts:
            (optional) Options to filter proxies retrieved by collector.
        :type filter_opts: dict or None
        :return:
            The retrieved proxies or None if no proxy found (either because none exist in internal store or none matched
            filter_opts).
        :rtype: List of Proxy or None
        :raises InvalidFilterOptionError:
            If `filter_opts` is not a dictionary or defines an invalid filter.
        """
        self._validate_filter_opts(filter_opts)

        combined_filter_opts = dict()
        self._extend_filter(combined_filter_opts, self._filter_opts)
        self._extend_filter(combined_filter_opts, filter_opts)

        self._refresh_resources(False)
        return self._store.get_proxies(combined_filter_opts, self._blacklist)

    def remove_blacklist(self, proxies=None, host=None, port=None):
        """Removes proxies from the blacklist.

        Either a single or sequence of proxies should be given, or a host and port number combination.

        :param proxies:
            (optional) A single or sequence of proxies to blacklist.
        :param host:
            (optional) The host IP of the proxy.
        :param port:
            (optional) The port number of the proxy.
        :type proxies: Proxy or iterable or None
        :type host: str or None
        :type port: str or None
        :raises ValueError:
            If neither proxies nor host and port are given.
        """
        if proxies is None and None in (host, port):
            raise ValueError('Either proxies or host and port should be given')

        if proxies is None:
            proxies = {(host, port), }
        elif not is_iterable(proxies):
            proxies = {(proxies[0], proxies[1]), }
        else:
            proxies = {(p[0], p[1]) for p in proxies}

        self._blacklist.difference_update(proxies)

    def remove_proxy(self, proxies):
        """Removes a proxy from the internal store.

        This is different from blacklisting as the blacklist will prevent a proxy from ever being retrieved, while this
        function simply removes it from the internal store. The proxy can still be added back to the internal store if
        it is retrieved via refresh.

        :param proxies:
            A single or sequence of proxies to remove from the internal store.
        :type proxies: Proxy or iterable
        :raises InvalidResourceTypeError:
            If any of the proxies specified have an invalid source (i.e. resource type).
        """
        if proxies is None:
            return

        if not is_iterable(proxies):
            proxies = {proxies, }
        else:
            proxies = set(proxies)

        for proxy in proxies:
            resource_type = proxy.source
            if resource_type not in self._resource_map:
                raise InvalidResourceTypeError(
                    '{} is not a valid resource type'.format(resource_type))

            id = self._resource_map[resource_type]['id']
            self._store.remove_proxy(id, proxy)

    def refresh_proxies(self, force=True):
        """Refreshes the proxies.

        This is used to refresh the proxies without retrieving one from the internal store. Defaults to forcing a
        refresh regardless of the last refresh performed.

        :param force:
            Whether to force a refresh. If True, a refresh is always performed; otherwise it is only done if a refresh
            hasn't occurred within the collector's `refresh_interval`. Defaults to True.
        :type force: bool
        """
        self._refresh_resources(force)
