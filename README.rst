Proxy Scrape
============

.. image:: https://img.shields.io/travis/JaredLGillespie/proxyscrape.svg
    :alt: Travis
    :target: https://travis-ci.org/JaredLGillespie/proxyscrape
.. image:: https://img.shields.io/coveralls/github/JaredLGillespie/proxyscrape.svg
    :alt: Coveralls github
    :target: https://coveralls.io/github/JaredLGillespie/proxyscrape
.. image:: https://img.shields.io/pypi/v/proxyscrape.svg
    :alt: PyPI
    :target: https://pypi.org/project/proxyscrape/
.. image:: https://img.shields.io/pypi/wheel/proxyscrape.svg
    :alt: PyPI - Wheel
    :target: https://pypi.org/project/proxyscrape/
.. image:: https://img.shields.io/pypi/pyversions/proxyscrape.svg
    :alt: PyPI - Python Version
    :target: https://pypi.org/project/proxyscrape/
.. image:: https://img.shields.io/pypi/l/proxyscrape.svg
    :alt: PyPI - License
    :target: https://pypi.org/project/proxyscrape/

A library for retrieving free proxies (HTTP, HTTPS, SOCKS4, SOCKS5). Supports Python 2.7+ and 3.4+.

*NOTE: This library isn't designed for production use. It's advised to use your own proxies or purchase a service which
provides an API. These are merely free ones that are retrieved from sites and should only be used for development
or testing purposes.*

.. code-block:: python

    import proxyscrape

    collector = proxyscrape.create_collector('default', 'http')  # Create a collector for http resources
    proxy = collector.get_proxy({'country': 'united states'})  # Retrieve a united states proxy

Installation
------------

The latest version of proxyscrape is available via ``pip``:

.. code-block:: bash

    $ pip install proxyscrape

Alternatively, you can download and install from source:

.. code-block:: bash

    $ python setup.py install

Provided Proxies
----------------
Current proxies provided are scraped from various sites which offer free HTTP, HTTPS, SOCKS4, and SOCKS5 proxies; and
don't require headless browsers or selenium to retrieve. The list of sites proxies retrieved are shown below.

+--------------------+----------------+--------------------------------------------------+
| resource           | resource type  | url                                              |
+====================+================+==================================================+
| anonymous-proxy    | http, https    | https://free-proxy-list.net/anonymous-proxy.html |
+--------------------+----------------+--------------------------------------------------+
| free-proxy-list    | http, https    | https://free-proxy-list.net                      |
+--------------------+----------------+--------------------------------------------------+
| proxy-daily-http   | http           | http://www.proxy-daily.com                       |
| proxy-daily-socks4 | socks4         |                                                  |
| proxy-daily-socks5 | socks5         |                                                  |
+--------------------+----------------+--------------------------------------------------+
| socks-proxy        | socks4, socks5 | https://www.socks-proxy.net                      |
+--------------------+----------------+--------------------------------------------------+
| ssl-proxy          | https          | https://www.sslproxies.org                       |
+--------------------+----------------+--------------------------------------------------+
| uk-proxy           | http, https    | https://free-proxy-list.net/uk-proxy.html        |
+--------------------+----------------+--------------------------------------------------+
| us-proxy           | http, https    | https://www.us-proxy.org                         |
+--------------------+----------------+--------------------------------------------------+

See `Integration`_ section for additional proxies.

Getting Started
---------------

Proxy Scrape is a library aimed at providing an efficient an easy means of retrieving proxies for web-scraping
purposes. The proxies retrieved are available from sites providing free proxies. The proxies provided, as shown in the
above table, can be of one of the following types (referred to as a `resource type`): http, https, socks4, and socks5.

Collectors
^^^^^^^^^^
Collectors serve as the interface to retrieving proxies. They are instantiating at module-level and can be retrieved
and re-used in different parts of the application (similar to the Python `logging` library). Collectors can be created
and retrieved via the `create_collector(...)` and `get_collector(...)` functions.

.. code-block:: python

    from proxyscrape import create_collector, get_collector

    collector = create_collector('my-collector', ['socks4', 'socks5'])

    # Some other section of code
    collector = get_collector('my-collector')

Each collector should have a unique name and be initialized only once. Typically, only a single collector of a given
resource type should be utilized. Filters can then be applied to the proxies if specific criteria is desired.

When given one or more resources, the collector will use those to retrieve proxies. If one or more resource types
are given, the resources for each of the types will be used to retrieve proxies.

Once created, proxies can be retrieved via the `get_proxy(...)` or the `get_proxies(...)` function. This optionally takes a `filter_opts`
parameter which can filter by the following:

- ``code`` (us, ca, ...)
- ``country`` (united states, canada, ...)
- ``anonymous`` (True, False)
- ``type`` (http, https, socks4, socks5, ...)

.. code-block:: python

    from proxyscrape import create_collector

    collector = create_collector('my-collector', 'http')

    # Retrieve any http proxy
    proxy = collector.get_proxy()

    # Retrieve only 'us' proxies
    proxy = collector.get_proxy({'code': 'us'})

    # Retrieve only anonymous 'uk' or 'us' proxies
    proxy = collector.get_proxy({'code': ('us', 'uk'), 'anonymous': True})

    # Retrieve all 'ca' proxies
    proxies = collector.get_proxies({'code': 'ca'})

Filters can be applied to every proxy retrieval from the collector via `apply_filter(...)`. This is useful when the same
filter is expected for any proxy retrieved.

.. code-block:: python

    from proxyscrape import create_collector

    collector = create_collector('my-collector', 'http')

    # Only retrieve 'uk' and 'us' proxies
    collector.apply_filter({'code': 'us'})

    # Filtered proxies
    proxy = collector.get_proxy()

    # Clear filter
    collector.clear_filter()

Note that some filters may instead use specific resources to achieve the same results (i.e. 'us-proxy' or 'uk-proxy' for
'us' and 'uk' proxies).

Blacklists can be applied to a collector to prevent specific proxies from being retrieved. They accept either one or more Proxy
objects, or a host + port number combination and won't allow retrieval of matching proxies. Proxies can be individually removed
from blacklists or the entire blacklist can be cleared.

.. code-block:: python

    from proxyscrape import create_collector

    collector = create_collector('my-collector', 'http')

    # Add proxy to blacklist
    collector.blacklist_proxy(Proxy('192.168.1.1', '80', None, None, None, 'http', 'my-resource'))
    collector.blacklist_proxy(host='192.168.1.2', port='8080')

    # Blacklisted proxies won't be included
    proxy = get_proxy()

    # Remove individual proxies
    collector.remove_blacklist(host='192.168.1.1', port='80')

    # Clear blacklist
    collector.clear_blacklist()


Instead of permanently blacklisting a particular proxies, a proxy can instead be removed from internal memory. This
allows it to be re-added to the pool upon a subsequent refresh.

.. code-block:: python

    from proxyscrape import create_collector

    collector = create_collector('my-collector', 'http')

    # Remove proxy from internal pool
    collector.remove_proxy(Proxy('192.168.1.1', '80', None, None, 'http', 'my-resource'))


Apart from automatic refreshes when retrieving proxies, they can also be forcefully refreshed via the
`refresh_proxies(...)` function.

.. code-block:: python

    from proxyscrape import create_collector

    collector = create_collector('my-collector', 'http')

    # Forcefully refresh
    collector.refresh_proxies(force=True)

    # Refresh only if proxies not refreshed within `refresh_interval`
    collector.refresh_proxies(force=False)

Resources
^^^^^^^^^
Resources refer to a specific function that retrieves a set of proxies; the currently implemented proxies are all
retrieves from scraping a particular web site.

Additional user-defined resources can be added to the pool of proxy retrieval functions via the `add_resource(...)`
function. Resources can belong to multiple resource types.

.. code-block:: python

    from proxyscrape import add_resource

    def func():
        return {Proxy('192.168.1.1', '80', 'us', 'united states', False, 'http', 'my-resource'), }

    add_resource('my-resource', func, 'http')

As shown above, a resource doesn't necessarily have to scrape proxies from a web site. It can be return a hard-coded
list of proxies, make a call to an api, read from a file, etc.

The set of library- and user-defined resources can be retrieved via the `get_resources(...)` function.

.. code-block:: python

    from proxyscrape import get_resources
    resources = get_resources()

Resource Types
^^^^^^^^^^^^^^
Resource types are groupings of resources that can be specified when defining a collector (opposed to giving a
collection of resources.

Additional user-defined resource types can be added via the `add_resource_type(...)` function. Resources can optionally
be added to a resource type when defining it.

.. code-block:: python

    from proxyscrape import add_resource_type
    add_resource_type('my-resource-type')
    add_resource_type('my-other-resource-type', 'my-resource')  # Define resources for resource type

The set of library- and user-defined resource types can be retrieved via the `get_resource_types(...)` function.

.. code-block:: python

    from proxyscrape import get_resource_types
    resources = get_resource_types()


.. _Integration:

Integration
-----------

Integrations are proxy implementations that are specific to a particular website or API and have a distinctively
separate use case.

ProxyScrape
^^^^^^^^^^^
The `ProxyScrape.com API`_ provides a means of accessing thousands of proxies of various types (HTTP, SOCKS4, SOCKS5) in
an efficient manner. These are vetted and validated with a minimal response time.

The `get_proxyscrape_resource(...)` function is used to dynamically create a new resource for using the proxyscrape API.
The resource name can then be added to a resource type and used like any other library- or user-defined resource. The
following parameters are used for the API:

- ``proxytype`` (http, socks4, socks5, all)
- ``timeout`` (milliseconds > 0)
- ``ssl`` (yes, no, all)
- ``anonymity`` (elite, anonymous, transparent, all)
- ``country`` (any Alpha 2 ISO country code, all)

.. code-block:: python

    from proxyscrape import get_proxyscrape_resource
    resource_name = get_proxyscrape_resource(proxytype='http', timeout=5000, ssl='yes', anonymity='all', country='us')


.. _ProxyScrape.com API: https://proxyscrape.com/en/api

Contribution
------------

Contributions or suggestions are welcome! Feel free to `open an issue`_ if a bug is found or an enhancement is desired,
or even a `pull request`_.

.. _open an issue: https://github.com/jaredlgillespie/proxyscrape/issues
.. _pull request: https://github.com/jaredlgillespie/proxyscrape/compare

Changelog
---------

All changes and versioning information can be found in the `CHANGELOG`_.

.. _CHANGELOG: https://github.com/JaredLGillespie/proxyscrape/blob/master/CHANGELOG.rst

License
-------

Copyright (c) 2018 Jared Gillespie. See `LICENSE`_ for details.

.. _LICENSE: https://github.com/JaredLGillespie/proxyscrape/blob/master/LICENSE.txt
