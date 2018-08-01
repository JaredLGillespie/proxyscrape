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

__all__ = ['add_resource', 'add_resource_type', 'create_collector', 'get_collector', 'get_resource_types',
           'get_resources']


from threading import Lock

from .errors import CollectorAlreadyDefinedError, CollectorNotFoundError, InvalidFilterOptionError, \
                    InvalidResourceAttributeError, InvalidResourceError, InvalidResourceTypeError, \
                    ResourceAlreadyDefinedError
from .scrapers import RESOURCE_MAP, RESOURCE_TYPE_MAP, ProxyResource
from .stores import Store, FILTER_OPTIONS


# TODO: Ensure thread-safe locks around collector creation / retrieval
# TODO: Ensure other thread-safe operations...

# Module-level references to collectors
COLLECTORS = {}
_collector_lock = Lock()
_resource_lock = Lock()
_resource_type_lock = Lock()


def _is_iterable(obj):
    if isinstance(obj, str):
        return False

    try:
        iter(obj)
        return True
    except TypeError:
        return False


def add_resource(name, resource, resource_types):
    if resource in RESOURCE_MAP:
        raise ResourceAlreadyDefinedError(f'{resource} is already defined')

    if not _is_iterable(resource_types):
        resource_types = {resource_types, }

    for attr in {'url', 'func'}:
        if attr not in resource:
            raise InvalidResourceAttributeError(f'{attr} not defined for resource')

    for resource_type in resource_types:
        if resource_type not in RESOURCE_TYPE_MAP:
            raise InvalidResourceTypeError(f'{resource_type} is not a defined resource type')

    with _resource_lock:
        # Ensure not added by the time entered lock
        if resource in RESOURCE_MAP:
            raise ResourceAlreadyDefinedError(f'{resource} is already defined')

        RESOURCE_MAP[name] = resource

        for resource_type in resource_types:
            RESOURCE_TYPE_MAP[resource_type] = resource


def add_resource_type(name):
    if name not in RESOURCE_TYPE_MAP:
        with _resource_type_lock:
            # Ensure not added by the time entered lock
            if name not in RESOURCE_TYPE_MAP:
                RESOURCE_TYPE_MAP[name] = set()


def create_collector(name, resource_types, refresh_interval=3600, resources=None):
    if name in COLLECTORS:
        raise CollectorAlreadyDefinedError(f'{name} already defined as a collector')

    with _collector_lock:
        # Ensure not added by the time entered lock
        if name in COLLECTORS:
            raise CollectorAlreadyDefinedError(f'{name} already defined as a collector')

        collector = Collector(resource_types, refresh_interval, resources)
        COLLECTORS[name] = collector
        return collector


def get_collector(name):
    if name in COLLECTORS:
        return COLLECTORS[name]

    raise CollectorNotFoundError(f'{name} is not a defined collector')


def get_resource_types():
    return RESOURCE_TYPE_MAP.keys()


def get_resources():
    return RESOURCE_MAP.keys()


class Collector:
    def __init__(self, resource_types, refresh_interval, resources):
        self._store = Store()
        self._blacklist = set()
        self._resource_types = set(resource_types) if _is_iterable(resource_types) else {resource_types, }

        # Input validations
        self._validate_resource_types(self._resource_types)
        resources = self._parse_resources(self._resource_types, resources)
        self._validate_resources(resources)

        self._resource_map = self._create_resource_map(resources, refresh_interval)
        self._filter_opts = {'version': self._resource_types.copy()}

    def _create_resource_map(self, resources, refresh_interval):
        resource_map = dict()
        for resource in resources:
            id = self._store.add_store()
            url = RESOURCE_MAP[resource]['url']
            func = RESOURCE_MAP[resource]['func']
            resource_map[resource] = {
                'proxy-resource': ProxyResource(url, func, refresh_interval),
                'id': id
            }

        return resource_map

    def _extend_filter(self, existing_filter_opts, new_filter_opts):
        if not new_filter_opts:
            return

        for key, value in new_filter_opts.items():
            if not _is_iterable(value):
                value = {value, }
            value = set(value)

            if key in existing_filter_opts:
                existing_filter_opts[key].update(value)
            else:
                existing_filter_opts[key] = value

    def _parse_resources(self, resource_types, resources):
        # Retrieve defaults if none specified
        if resources is None:
            res = set()
            for resource_type in resource_types:
                if resource_type in RESOURCE_TYPE_MAP:
                    res.update(RESOURCE_TYPE_MAP[resource_type])
            return res

        if _is_iterable(resources):
            return set(resources)
        else:
            return {resources, }

    def _refresh_resources(self, force):
        # TODO: Need to do asynchronously + concurrently
        for resource in self._resource_map.values():
            refreshed, proxies = resource['proxy-resource'].refresh(force)

            if refreshed:
                self._store.update_store(resource['id'], proxies)

    def _validate_filter_opts(self, filter_opts):
        if not filter_opts:
            return

        if not isinstance(filter_opts, dict):
            raise InvalidFilterOptionError(f'{filter_opts} must be a dictionary')

        for key in filter_opts:
            if key not in FILTER_OPTIONS:
                raise InvalidFilterOptionError(f'{key} is an invalid filter option')

    def _validate_resource_types(self, resource_types):
        if resource_types is None:
            raise InvalidResourceTypeError(f'a resource type must be specified')

        if _is_iterable(resource_types):
            if set(resource_types).difference(RESOURCE_TYPE_MAP.keys()):
                raise InvalidResourceTypeError(f'{resource_types} defined an invalid resource type')
        else:
            if resource_types not in RESOURCE_TYPE_MAP:
                raise InvalidResourceTypeError(f'{resource_types} is an invalid resource type')

    def _validate_resources(self, resources):
        for resource in resources:
            if resource not in RESOURCE_MAP:
                raise InvalidResourceError(f'{resource} is an invalid resource')

    def apply_filter(self, filter_opts):
        self._validate_filter_opts(filter_opts)
        self._extend_filter(self._filter_opts, filter_opts)

    def blacklist_proxy(self, proxies):
        if not _is_iterable(proxies):
            proxies = {proxies, }
        proxies = set(proxies)

        self._blacklist.update(proxies)

    def clear_blacklist(self):
        self._blacklist.clear()

    def clear_filter(self):
        self._filter_opts = {'version': self._resource_types.copy()}

    def get_proxy(self, filter_opts=None):
        self._validate_filter_opts(filter_opts)

        combined_filter_opts = dict()
        self._extend_filter(combined_filter_opts, self._filter_opts)
        self._extend_filter(combined_filter_opts, filter_opts)

        self._refresh_resources(False)
        return self._store.get_proxy(filter_opts, self._blacklist)

    def remove_proxy(self, proxies):
        if not _is_iterable(proxies):
            proxies = {proxies, }

        for proxy in proxies:
            resource_type = proxy.source
            id = self._resource_map[resource_type]['id']
            self._store.remove_proxy(id, proxy)

    def refresh_proxies(self):
        self._refresh_resources(True)
