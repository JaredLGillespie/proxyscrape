Changelog
=========
All notable changes to this project will be documented in this file.

The format is based on `Keep a Changelog`_ and this project adheres to `Semantic Versioning`_.

.. _Keep a Changelog: http://keepachangelog.com/en/1.0.0/
.. _Semantic Versioning: http://semver.org/spec/v2.0.0.html

`Unreleased`_
-------------

`0.3.0`_ - 2019-08-18
---------------------
Fixed
^^^^^
- proxyscrape integration user-defined country codes actually work
- proxyscrape integration type properly defined for 'all'
- proxy-daily scrapers fixed (website changed)

Added
^^^^^
- Python 3.7 Support
- get_proxies(...) added for retrieving all proxies instead of just 1 (i.e. get_proxy(...))

Changed
^^^^^^^
- Implicit filtering of proxies based on resource_type name removed

`0.2.1`_ - 2019-06-19
---------------------
Fixed
^^^^^
- proxyscrape API URL fixed.
- Catching requests library errors (connection, timeout, etc.).

`0.2.0`_ - 2019-02-07
---------------------
Added
^^^^^
- Integration with proxyscrape.com
- Able to remove individual proxies from blacklist

Changed
^^^^^^^
- Blacklist is now by host + IP only

`0.1.1`_ - 2018-12-03
---------------------
Added
^^^^^
- Python 2.7, 3.4, and 3.5 Support

`0.1.0`_ - 2018-08-26
---------------------
Added
^^^^^
- Initial Version

.. _Unreleased: https://github.com/JaredLGillespie/proxyscrape/compare/v0.3.0...HEAD
.. _0.3.0: https://github.com/JaredLGillespie/proxyscrape/releases/tag/v0.3.0
.. _0.2.1: https://github.com/JaredLGillespie/proxyscrape/releases/tag/v0.2.1
.. _0.2.0: https://github.com/JaredLGillespie/proxyscrape/releases/tag/v0.2.0
.. _0.1.1: https://github.com/JaredLGillespie/proxyscrape/releases/tag/v0.1.1
.. _0.1.0: https://github.com/JaredLGillespie/proxyscrape/releases/tag/v0.1.0
