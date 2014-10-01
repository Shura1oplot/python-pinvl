# -*- coding: utf-8 -*-

from dateutil.parser import parse
from datetime import datetime
from ..validators import TypeConvert, DataError
from .._compat import *


class DateTime(TypeConvert):

    """
    Class for support parsing date im RFC3339 formats via dateutil.parse helper
    """

    _convertable = string_types
    _value_type = datetime

    def _convert(self, value):
        if isinstance(self, self._value_type):
            return value

        if not isinstance(value, self._convertable):
            raise self._cannot_convert()

        try:
            value = parse(value)
        except ValueError:
            raise DataError("value cannot be parsed as date")
