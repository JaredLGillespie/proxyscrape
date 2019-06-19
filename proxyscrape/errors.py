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


class ProxyScrapeBaseException(Exception):
    """Base Exception for Proxy Scrape."""


class CollectorAlreadyDefinedError(ProxyScrapeBaseException):
    """Collector Already Defined Error."""


class CollectorNotFoundError(ProxyScrapeBaseException):
    """Collector Not Found Error."""


class InvalidFilterOptionError(ProxyScrapeBaseException):
    """Invalid Filter Option Error."""


class InvalidHTMLError(ProxyScrapeBaseException):
    """Invalid HTML Error."""


class InvalidResourceError(ProxyScrapeBaseException):
    """Invalid Resource Error."""


class InvalidResourceTypeError(ProxyScrapeBaseException):
    """Invalid Resource Type Error."""


class RequestNotOKError(ProxyScrapeBaseException):
    """Request Not OK Error."""


class RequestFailedError(ProxyScrapeBaseException):
    """Request Failed Error."""


class ResourceAlreadyDefinedError(ProxyScrapeBaseException):
    """Resource Already Defined Error."""


class ResourceTypeAlreadyDefinedError(ProxyScrapeBaseException):
    """Resource Type Already Defined Error."""
