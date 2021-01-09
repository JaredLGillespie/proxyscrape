#!/usr/bin/python3.8

"""Creats a proxy filter that filters proxies based on
different proxy functions"""

from .proxyscrape import (
    create_collector,
    get_collector
)
from .shared import Proxy
from .proxyscrape import Collector

import requests
import concurrent.futures

class Proxy_filter():
    """Filters proxies based on different paramaters
    """

    def __new__(cls, proxies):
        """Check if the parameters passed are equal before 
	creating the instance"""
        if not isinstance(proxies, list):
            return None
        if not all(isinstance(proxy, Proxy) for proxy in proxies):
            return None
        return super().__new__(Proxy_filter)

    def __init__(self, proxies):
        """Stores the prox list as a class variable"""
        self.__proxies = proxies

    def uniqueCountry(self):
        """Returns a list of proxies whose country id unique 
	to each other"""
        proxies = []
        countries = []
        for proxy in self.__proxies:
            if proxy.country not in countries and proxy.country != None:
                countries += [proxy.country]
                proxies += [proxy]
        return proxies

    def workingProxies(self, timeout=3, test_url='https://httpbin.org/ip'):
        """Concurrently checks if the proxies are
	accessible from your network, and returns a list
	of the working once. 

	@timout: could be set to determine the waiting time, 6 is the default
        @test_url: test_url is the site used to test the proxies, 'https://httpbin.org/ip' is the default
	"""
        proxies = []
        def test_proxy(proxy):
            """Takes a proxy object and checks if it works for 
            test_url in timeout time"""
            proxy_port = ":".join([proxy.host, proxy.port])
            try:
                r = requests.get(test_url, proxies={'http':proxy_port, 'https':proxy_port}, timeout=timeout)
                proxies.append(proxy)
            except Exception:
                pass
        with concurrent.futures.ThreadPoolExecutor() as exector:
            exector.map(test_proxy, self.__proxies)
        return proxies

    def get_proxies(self):
        return self.__proxies

    def set_proxies(self, new_proxy_list):
        """set the __proxies private varaibel"""
        if not isinstance(new_proxy_list, list):
            return
        if not all(isinstance(proxy, Proxy) for proxy in new_proxy_list):
            return
        self.__proxies = new_proxy_list
    proxies = property(get_proxies, set_proxies)
       

if __name__ == '__main__':
    collector = create_collector('Proxy_collector', ['https', 'http'])
    proxies = collector.get_proxies()

    # filter the working proxies only
    filterer = Proxy_filter(proxies)
    working_proxies = filterer.workingProxies()

    # Filter one ip from each country
    filterer.set_proxies(working_proxies)
    uniqs = filterer.uniqueCountry()

    print(uniqs, len(uniqs))
