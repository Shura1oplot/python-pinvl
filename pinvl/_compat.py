# -*- coding: utf-8 -*-

import sys


__all__ = (
    "PY2", "PY3",
    "string_types", "integer_types", "class_types", "text_type", "binary_type",
    "map", "filter", "zip",
    "iterkeys", "itervalues", "iteritems",
    "implements_metaclass", "metaclass",
    "Undefined",
    "urlparse",
)


# PORTABLE:CODE
PY2 = sys.version_info[0] == 2
PY3 = sys.version_info[0] == 3


# types
if PY2:
    import types
    string_types = (str, unicode),
    integer_types = (int, long)
    class_types = (type, types.ClassType)
    text_type = unicode
    binary_type = str

else:
    string_types = (str, ),
    integer_types = (int, ),
    class_types = (type, ),
    text_type = str
    binary_type = bytes


# map, filter, zip
if PY2:
    try:
        from future_builtins import map, filter, zip
    except ImportError:
        from itertools import (
            imap as map,
            ifilter as filter,
            izip as zip,
        )

else:
    from builtins import map, filter, zip


# iterkeys, itervalues, iteritems
if PY2:
    def iterkeys(mapping):
        try:
            return mapping.iterkeys()
        except AttributeError:
            return iter(mapping.keys())

    def itervalues(mapping):
        try:
            return mapping.itervalues()
        except AttributeError:
            return iter(mapping.values())

    def iteritems(mapping):
        try:
            return mapping.iteritems()
        except AttributeError:
            return iter(mapping.items())

else:
    def iterkeys(mapping):
        return iter(mapping.keys())

    def itervalues(mapping):
        return iter(mapping.values())

    def iteritems(mapping):
        return iter(mapping.items())


# metaclass
_metaclass_container_name = "__metaclass_container__"


def implements_metaclass(meta):
    orig_init = meta.__init__

    def __init__(cls, name, bases, dct):
        if name == _metaclass_container_name:
            type.__init__(cls, name, (object, ), dct)
            return

        bases = tuple(
            base for base in bases
            if base.__name__ != _metaclass_container_name
        )

        orig_init(cls, name, bases, dct)

    meta.__init__ = __init__

    return meta


def metaclass(meta):
    return meta(_metaclass_container_name, (object, ), {})


# Undefined
class UndefinedType(object):

    __slots__ = ()

    def __nonzero__(self):
        return False

    def __str__(self):
        return "Undefined"

    def __repr__(self):
        return "Undefined"

Undefined = UndefinedType()


# urlparse
if PY2:
    import urlparse

else:
    import urllib.parse as urlparse
