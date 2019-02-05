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

"""A library for retrieving free proxies (HTTP, HTTPS, SOCKS4, SOCKS5).

Basic usage:
    >>> import proxyscrape
    >>> collector = proxyscrape.create_collector('default', 'http')  # Create a collector for http resources
    >>> proxy = collector.get_proxy({'country': 'united states'})  # Retrieve a united states proxy

The main library components are:
    - Collector - responsible for scraping resources for proxies
    - Resource - a url + function combination for scraping proxies
    - Resource Type - a grouping of resources (i.e. http, https, socks4, socks5)

This exports:
    - add_resource(...) adds a new resource to be scraped
    - add_resource_type(...) adds a new resource type
    - create_collector(...) create a new collector to scrape resources
    - get_collector(...) retrieves a created collector
    - get_resource_type(...) retrieves all defined resource types
    - get_resources(...) retrieves all defined resources
"""

from __future__ import absolute_import

from .errors import (
    ProxyScrapeBaseException,
    CollectorAlreadyDefinedError,
    CollectorNotFoundError,
    InvalidFilterOptionError,
    InvalidHTMLError,
    InvalidResourceError,
    InvalidResourceTypeError,
    RequestNotOKError,
    ResourceAlreadyDefinedError,
    ResourceTypeAlreadyDefinedError
)
from .integration import get_proxyscrape_resource
from .proxyscrape import (
    create_collector,
    get_collector
)
from .scrapers import (
    add_resource,
    add_resource_type,
    get_resource_types,
    get_resources
)
from .shared import Proxy
