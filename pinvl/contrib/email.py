# -*- coding: utf-8 -*-

import re
import encodings.idna  # it enables idna encode/decode in python3
from ..validators import String, DataError
from .._compat import *


class Email(String):

    """
    >>> Email().check("someone@example.net")
    'someone@example.net'
    >>> extract_error(Email(),'someone@example') # try without domain-part
    'value is not a valid email address'
    >>> str(Email().check('someone@пример.рф')) # try with `idna` encoding
    'someone@xn--e1afmkfd.xn--p1ai'
    >>> (Email() >> (lambda m: m.groupdict()['domain'])).check('someone@example.net')
    'example.net'
    >>> extract_error(Email(),'foo')
    'value is not a valid email address'
    """

    _email_regex = re.compile(
        r"(?P<name>^[-!#$%&'*+/=?^_`{}|~0-9A-Z]+(\.[-!#$%&'*+/=?^_`{}|~0-9A-Z]+)*"  # dot-atom
        r'|^"([\001-\010\013\014\016-\037!#-\[\]-\177]|\\[\001-011\013\014\016-\177])*"'  # quoted-string
        r')@(?P<domain>(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)$)'  # domain
        r'|\[(25[0-5]|2[0-4]\d|[0-1]?\d?\d)(\.(25[0-5]|2[0-4]\d|[0-1]?\d?\d)){3}\]$',  # literal form, ipv4 address (SMTP 4.1.3)
        re.IGNORECASE
    )

    def __init__(self):
        super(Email, self).__init__(self._email_regex)

    def _check(self, value):
        try:
            return super(Email, self)._check(value)
        except DataError:
            if value and isinstance(value, bytes):
                value = value.decode("utf-8")

            # Trivial case failed. Try for possible IDN domain-part
            if value and "@" in value:
                parts = value.split("@")

                try:
                    parts[-1] = parts[-1].encode("idna").decode('ascii')
                except UnicodeError:
                    pass
                else:
                    try:
                        return super(Email, self)._check("@".join(parts))
                    except DataError:
                        # Will fail with main error
                        pass

        raise DataError("value is not a valid email address")
