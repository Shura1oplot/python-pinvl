# -*- coding: utf-8 -*-

"""
Pinvl is tiny library for data validation. It provides several primitives
to validate complex data structures. Look at class docs for usage examples.
"""

import sys
from .validators import *
from .validators import __all__ as __validators_all__


__version_info__ = (0, 1, 0)
__version__ = ".".join(map(str, __version_info__))


__all__ = list(__validators_all__)

ENTRY_POINT = "pinvl"


def _load_contrib():
    from pkg_resources import iter_entry_points, DistributionNotFound

    for entry_point in iter_entry_points(ENTRY_POINT):
        try:
            cls = entry_point.load()
        except (ImportError, DistributionNotFound):
            continue

        setattr(sys.modules[__name__], cls.__name__, cls)
        __all__.append(cls.__name__)

_load_contrib()
