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

from proxyscrape.scrapers import RESOURCE_MAP, RESOURCE_TYPE_MAP, ProxyResource
from proxyscrape.stores import Store

__all__ = ['Collector', 'add_resource', 'add_resource_type', 'get_resource_types', 'get_resources']

# TODO: Alter filters based on 'country', 'anonymous', 'https', 'version'


def _is_iterable(obj):
    try:
        iter(obj)
        return True
    except TypeError:
        return False


def add_resource(name, resource, resource_types):
    if not _is_iterable(resource_types):
        resource_types = {resource_types, }

    for attr in {'url', 'func'}:
        if attr not in resource:
            # TODO: Use custom exceptions
            raise ValueError(f'{attr} not defined for resource')

    RESOURCE_MAP[name] = resource

    for resource_type in resource_types:
        # TODO: Use custom exceptions
        if resource_type not in RESOURCE_TYPE_MAP:
            raise ValueError(f'{resource_type} is not a defined resource type')

        RESOURCE_TYPE_MAP[resource_type] = resource


def add_resource_type(name):
    if name not in RESOURCE_TYPE_MAP:
        RESOURCE_TYPE_MAP[name] = set()


def get_resource_types():
    return RESOURCE_TYPE_MAP.keys()


def get_resources():
    return RESOURCE_MAP.keys()


# TODO: Add way to create collector and create internal store with name

class Collector:
    def __init__(self, resource_types, refresh_interval=3600, resources=None):
        # Input validations
        self._validate_resource_types(resource_types)
        self._validate_resources(resources)

        self._store = Store()
        self._black_list = set()
        self._resource_types = set(resource_types) if _is_iterable(resource_types) else {resource_types, }
        self._resource_map = self._create_resource_map(self._resource_types, resources, refresh_interval)
        self._filter_opts = dict()

    def _create_resource_map(self, resource_types, resources, refresh_interval):
        resources = self._parse_resources(resource_types, resources)
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
                if resource_type in resources:
                    res.update(resources[resource_type])
            return res

    def _refresh_resources(self):
        # TODO: Need to do asynchronously + parallel
        for resource in self._resource_map:
            refreshed, proxies = resource['proxy-resource'].refresh()

            if refreshed:
                self._store.update_store(resource['id'], proxies)

    def _validate_resource_types(self, resource_types):
        # TODO: Use custom exceptions
        if resource_types is None:
            raise ValueError(f'a resource type must be specified')

        if _is_iterable(resource_types):
            if resource_types not in RESOURCE_TYPE_MAP:
                raise ValueError(f'{resource_types} is an invalid resource type')

        elif set(resource_types).difference(RESOURCE_TYPE_MAP.keys()):
            raise ValueError(f'{resource_types} defined an invalid resource type')

    def _validate_resources(self, resources):
        for resource in resources:
            if resource not in RESOURCE_MAP:
                raise ValueError(f'{resource} is an invalid resource')

    def apply_filter(self, filter_opts):
        if not isinstance(filter_opts, dict):
            raise ValueError(f'{filter_opts} must be a dictionary')

        self._extend_filter(self._filter_opts, filter_opts)

    def blacklist_proxy(self, proxies):
        if not _is_iterable(proxies):
            proxies = {proxies, }
        proxies = set(proxies)

        self._black_list.update(proxies)

    def clear_blacklist(self):
        self._black_list.clear()

    def clear_filter(self):
        self._filter_opts.clear()

    def get_proxy(self, filter_opts=None):
        if not isinstance(filter_opts, dict):
            raise ValueError(f'{filter_opts} must be a dictionary')

        combined_filter_opts = dict()
        self._extend_filter(combined_filter_opts, self._filter_opts)
        self._extend_filter(combined_filter_opts, filter_opts)

    def remove_proxy(self, proxies):
        if not _is_iterable(proxies):
            proxies = {proxies, }

        for proxy in proxies:
            resource_type = proxy.source
            id = self._resource_map[resource_type]['id']
            self._store.remove_proxy(id, proxy)
