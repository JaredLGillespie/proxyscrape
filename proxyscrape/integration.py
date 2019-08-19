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


__all__ = ['get_proxyscrape_resource']


from .errors import (
    InvalidHTMLError,
    InvalidResourceTypeError,
    ResourceAlreadyDefinedError
)
from .scrapers import add_resource
from .shared import (
    Proxy,
    request_proxy_list
)


def get_proxyscrape_resource(proxytype='all', timeout=10000, ssl='all', anonymity='all', country='all'):
    """Creates proxy resources for proxyscrape.com.

    Resources are created to retrieve proxies from proxyscrape.com. Resources are named as a combination of the
    parameters used. Calling this function multiple times with different parameters will create different resources.

    :param proxytype:
        (optional) The type of proxy. Can be one of 4 values: 'http', 'socks4', 'socks5', 'all. Defaults to 'all'.
    :param timeout:
        (optional) The minimal response time of the proxy, specified in milliseconds. Defaults to 10000ms.
    :param ssl:
        (optional). Whether the proxies should be over ssl. Can be one of 3 values: 'yes', 'no', 'all'. Defaults to
        'all'.
    :param anonymity:
        The anonymity level of the proxies. Can be one of 4 values: 'elite', 'anonymous', 'transparent', 'all'.
    :param country:
        The countries the proxies should correspond to. Should be any Alpha 2 ISO country code, or 'all'. Defaults to
        'all'.
    :type proxytype: string
    :type timeout: int
    :type ssl: string
    :type anonymity: string
    :type country: string
    :return:
        Returns the name of the new resource.
    :rtype: string
    :raises ValueError:
        If any of the provided parameters are invalid.
    """
    proxytype = proxytype.lower()
    ssl = ssl.lower()
    anonymity = anonymity.lower()
    country = country.upper()

    if proxytype not in {'http', 'socks4', 'socks5', 'all'}:
        raise ValueError('proxytype %s is not valid' % proxytype)

    if timeout <= 0:
        raise ValueError('timeout %s should be an integer greater than 0' % proxytype)

    if ssl not in {'yes', 'no', 'all'}:
        raise ValueError('ssl %s is not valid' % ssl)

    if anonymity not in {'elite', 'anonymous', 'transparent', 'all'}:
        raise ValueError('anonymity %s is not valid' % anonymity)

    if len(country) != 2 and country != 'ALL':
        raise ValueError('country %s is not valid' % country)

    name = '|'.join(['proxyscrape',
                     'proxytype=%s' % proxytype,
                     'timeout=%s' % timeout,
                     'ssl=%s' % ssl,
                     'anonymity=%s' % anonymity,
                     'country=%s' % country])

    url = 'https://api.proxyscrape.com?request=getproxies' + \
          '&proxytype=%s' % proxytype + \
          '&timeout=%s' % timeout + \
          '&ssl=%s' % ssl + \
          '&anonymity=%s' % anonymity + \
          '&country=%s' % country

    def func():
        response = request_proxy_list(url)

        try:
            proxies = set()
            code = None if country.lower() == 'all' else country
            anonymous = anonymity in {'elite', 'anonymous'}
            type = None if proxytype == 'all' else proxytype

            for line in response.text.split():
                host, port = map(str, line.split(':'))
                proxies.add(Proxy(host, port, code, None, anonymous, type, name))

            return proxies
        except (AttributeError, ValueError):
            raise InvalidHTMLError()

    try:
        add_resource(name, func)
    except (InvalidResourceTypeError, ResourceAlreadyDefinedError):
        pass

    return name
