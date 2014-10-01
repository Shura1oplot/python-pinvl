# -*- coding: utf-8 -*-

from bson import ObjectId

from ..validators import TypeConvert
from .._compat import *


class MongoId(TypeConvert):

    """
    Type check & convert bson.ObjectId values
    """

    _convertable = string_types
    _value_type = ObjectId
