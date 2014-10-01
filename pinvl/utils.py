# -*- coding: utf-8 -*-

"""
There will be small helpers to render forms with exist validators for DRY.
"""

from collections import Mapping, Sequence
from itertools import groupby
from ._compat import *


def recursive_unfold(data, prefix="", delimeter="__"):

    def concat(value):
        return "{}{}{!s}".format(
            prefix,
            delimeter if prefix else "",
            value
        )

    def unfold_sequence(data):
        for i, item in enumerate(data):
            for pair in recursive_unfold(item, concat(str(i)), delimeter):
                yield pair

    def unfold_mapping(data):
        for key, value in iteritems(data):
            for pair in recursive_unfold(value, concat(key), delimeter):
                yield pair

    if isinstance(data, Mapping):
        for pair in unfold_mapping(data):
            yield pair

    elif isinstance(data, Sequence):
        for pair in unfold_sequence(data):
            yield pair

    else:
        yield prefix, data


def unfold(data, prefix="", delimeter="__"):

    """
    >>> unfold({'a': 4, 'b': 5})
    {'a': 4, 'b': 5}
    >>> unfold({'a': [1, 2, 3]})
    {'a__1': 2, 'a__0': 1, 'a__2': 3}
    >>> unfold({'a': {'a': 4, 'b': 5}})
    {'a__a': 4, 'a__b': 5}
    >>> unfold({'a': {'a': 4, 'b': 5}}, 'form')
    {'form__a__b': 5, 'form__a__a': 4}
    """

    return dict(recursive_unfold(data, prefix, delimeter))


def fold(data, prefix="", delimeter="__"):

    """
    >>> fold({'a__a': 4})
    {'a': {'a': 4}}
    >>> fold({'a__a': 4, 'a__b': 5})
    {'a': {'a': 4, 'b': 5}}
    >>> fold({'a__1': 2, 'a__0': 1, 'a__2': 3})
    {'a': [1, 2, 3]}
    >>> fold({'form__a__b': 5, 'form__a__a': 4}, 'form')
    {'a': {'a': 4, 'b': 5}}
    >>> fold({'form__a__b': 5, 'form__a__a__0': 4, 'form__a__a__1': 7}, 'form')
    {'a': {'a': [4, 7], 'b': 5}}
    >>> fold({'form__1__b': 5, 'form__0__a__0': 4, 'form__0__a__1': 7}, 'form')
    [{'a': [4, 7]}, {'b': 5}]
    """

    def deep(data):
        if len(data) == 1 and len(data[0][0]) < 2:
            if data[0][0]:
                return {data[0][0][0]: data[0][1]}

            return data[0][1]

        collect = {}

        for key, group in groupby(data, lambda kv: kv[0][0]):
            nest_data = [(k[1:], v) for k, v in group]
            collect[key] = deep(nest_data)

        is_num = all(key.isdigit() for key in iterkeys(collect))

        if is_num:
            return [value for key, value in sorted(iteritems(collect))]

        return collect

    data_ = [(key.split(delimeter), value) for key, value in sorted(data.items())]
    result = deep(data_)

    return result[prefix] if prefix else result
