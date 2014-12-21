# -*- coding: utf-8 -*-

import re
import encodings.idna  # it enables idna encode/decode in python3
from ..validators import String, DataError
from .._compat import *


class URL(String):

    """
    >>> URL().check("http://example.net/resource/?param=value#anchor")
    'http://example.net/resource/?param=value#anchor'
    >>> str(URL().check(u"http://пример.рф/resource/?param=value#anchor"))
    'http://xn--e1afmkfd.xn--p1ai/resource/?param=value#anchor'
    """

    _url_regex = re.compile(
        r'^(?:http|ftp)s?://'  # http:// or https://
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|'  # domain...
        r'localhost|'  # localhost...
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
        r'(?::\d+)?'  # optional port
        r'(?:/?|[/?]\S+)$',
        re.IGNORECASE
    )

    def __init__(self):
        super(URL, self).__init__(self._url_regex)

    def _check(self, value):
        try:
            return super(URL, self)._check(value)
        except DataError:
            pass

        if not value:
            raise self._invalid_url()

        # Trivial case failed. Try for possible IDN domain-part
        if isinstance(value, binary_type):
            try:
                value = value.decode("utf-8")
            except UnicodeError:
                raise self._invalid_url()

        try:
            scheme, netloc, path, query, fragment = urlparse.urlsplit(value)
        except ValueError:
            raise self._invalid_url()

        try:
            netloc = netloc.encode("idna").decode("ascii")  # IDN -> ACE
        except UnicodeError:  # invalid domain part
            raise self._invalid_url()

        url = urlparse.urlunsplit((scheme, netloc, path, query, fragment))

        try:
            return super(URL, self)._check(url)
        except DataError:
            raise self._invalid_url()

    @staticmethod
    def _invalid_url():
        return DataError("value is not a valid URL")
