# -*- coding: utf-8 -*-

import copy
import re
import numbers
from ._compat import *


__all__ = ("Type", "Any", "Or", "Null", "Bool", "Float", "Int", "Atom",
           "String", "List", "Tuple", "Key", "Dict", "Mapping", "Enum",
           "Callable", "Call", "Forward", "DataError")


# PORTABLE:CODE
class DataError(ValueError):

    """
    Error with data preserve.
    `error` can be a message or None if error raised in childs.
    """

    def __init__(self, error=None):
        super(DataError, self).__init__()

        self.error = error

    def __str__(self):
        return str(self.error)

    def __repr__(self):
        return "{0}({1})".format(self.__class__.__name__, self)

    def as_dict(self):
        if not isinstance(self.error, dict):
            return self.error

        return dict((k, v.as_dict() if isinstance(v, self.__class__) else v)
                    for k, v in iteritems(self.error))


@implements_metaclass
class ValidatorMeta(type):

    """
    Metaclass for validators to make using "|" operator possible not only
    on instances but on classes.

    >>> Int | String
    <Or(<Int>, <String>)>
    >>> Int | String | Null
    <Or(<Int>, <String>, <Null>)>
    >>> (Int >> (lambda v: v if v ** 2 > 15 else 0)).check(5)
    5
    """

    def __or__(cls, other):
        return cls() | other

    def __rshift__(cls, other):
        return cls() >> other


class ValidatorBase(metaclass(ValidatorMeta), object):

    """
    Base class for validators, provides only one method for validation failure
    reporting.

    Check that converters can be stacked
    >>> (Int() >> (lambda x: x * 2) >> (lambda x: x * 3)).check(1)
    6

    Check order
    >>> (Int() >> float >> str).check(4)
    '4.0'
    """

    def __init__(self):
        super(ValidatorBase, self).__init__()

        self._converters = []

    def check(self, value):
        """
        Common logic. In subclasses you need to implement _check.
        """
        value = self._check(value)

        if self._converters:
            for converter in self._converters:
                value = converter(value)

            return value

        return self._converter_default(value)

    def _check(self, value):
        raise NotImplementedError()

    def _converter_default(self, value):  # pylint: disable=R0201
        """
        You can change default converter with '>>' operator or `append` method.
        """
        return value

    @staticmethod
    def _ensure_validator(validator):
        """
        Helper for complex validators, takes validator instance or class
        and returns validator instance.
        """
        if isinstance(validator, ValidatorBase):
            return validator

        if isinstance(validator, class_types):
            if issubclass(validator, ValidatorBase):
                return validator()

            return Type(validator)

        if callable(validator):
            return Call(validator)

        raise RuntimeError(("{0!r} should be instance or subclass of "
                            "ValidatorBase").format(validator))

    def append(self, converter):
        self._converters.append(converter)

    def __or__(self, other):
        return Or(self, other)

    def __rshift__(self, other):
        obj = copy.deepcopy(self)
        obj.append(other)
        return obj

    def __call__(self, value):
        return self.check(value)

    def repr(self, memo):  # pylint: disable=W0613
        return "<{0}>".format(self.__class__.__name__)

    def __repr__(self):
        return self.repr({})


class TypeConvert(ValidatorBase):

    _convertable = ()
    _value_type = type

    def _check(self, value):
        return self._convert(value)

    def _convert(self, value):
        if isinstance(value, self._value_type):
            return value

        if not isinstance(value, self._convertable):
            raise self._cannot_convert()

        try:
            return self._value_type(value)
        except ValueError:
            raise self._cannot_convert()

    def _cannot_convert(self):
        return DataError("value cannot be converted to {0}".format(self._value_type.__name__))


@implements_metaclass
class TypeMeta(ValidatorMeta):

    def __getitem__(cls, type_):
        return cls(type_)


class Type(metaclass(TypeMeta), ValidatorBase):

    """
    >>> Type(int)
    <Type(int)>
    >>> Type[int]
    <Type(int)>
    >>> c = Type[int]
    >>> c.check(1)
    1
    >>> extract_error(c, "foo")
    'value is not int'
    """

    def __init__(self, type_):
        super(Type, self).__init__()

        self.type = type_

    def _check(self, value):
        if not isinstance(value, self.type):
            raise DataError("value is not {0}".format(self.type.__name__))

        return value

    def repr(self, memo):
        return "<{0}({1})>".format(self.__class__.__name__, self.type.__name__)


class Any(ValidatorBase):

    """
    >>> Any()
    <Any>
    """

    def _check(self, value):
        return value


class Or(ValidatorBase):

    """
    >>> null_string = Or(String, Null)
    >>> null_string
    <Or(<String>, <Null>)>
    >>> null_string.check(None)
    >>> null_string.check("test")
    'test'
    >>> extract_error(null_string, 1)
    {'<Null>': 'value should be None', '<String>': 'value is not a string'}
    """

    def __init__(self, *validators):
        super(Or, self).__init__()

        self.validators = list(map(self._ensure_validator, validators))

    def _check(self, value):
        errors = {}

        for validator in self.validators:
            try:
                return validator.check(value)
            except DataError as e:
                errors.setdefault(repr(validator), []).append(e)

        for sncl_repr, err_lst in iteritems(errors):
            if len(err_lst) == 1:
                errors[sncl_repr] = err_lst[0]
            else:
                errors[sncl_repr] = DataError(dict(enumerate(err_lst)))

        raise DataError(errors)

    def __or__(self, validator):
        validators = self.validators[:]
        validators.append(validator)
        return self.__class__(*validators)

    def repr(self, memo):
        return "<{0}({1})>".format(
            self.__class__.__name__,
            ", ".join(validator.repr(memo) for validator in self.validators),
        )


class Null(ValidatorBase):

    """
    >>> Null()
    <Null>
    >>> Null().check(None)
    >>> extract_error(Null(), 1)
    'value should be None'
    """

    def _check(self, value):
        if value is not None:
            raise DataError("value should be None")

        return value


class Bool(ValidatorBase):

    """
    >>> Bool()
    <Bool>
    >>> Bool().check(convert=True)
    True
    >>> Bool().check(convert=False)
    False
    >>> extract_error(Bool(), 1)
    'value should be True or False'
    >>> extract_error(Bool(true), "aloha")
    'value cannot be converted to bool'
    >>> Bool(true).check(1)
    True
    >>> Bool(true).check(0)
    False
    >>> Bool(true).check("y")
    True
    >>> Bool(true).check("n")
    False
    >>> Bool(true).check("1")
    True
    >>> Bool(true).check("0")
    False
    >>> Bool(true).check("Yes")
    True
    >>> Bool(true).check("No")
    False
    """

    _convertable = string_types + integer_types

    _aliases_true  = frozenset((True,  1, "true",  "t"  "yes", "y", "1"))
    _aliases_false = frozenset((False, 0, "false", "f", "no",  "n", "0"))

    def __init__(self, convert=False):
        super(Bool, self).__init__()

        self.convert = convert

    def _check(self, value):
        if isinstance(value, bool):
            return value

        if not self.convert:
            raise DataError("value should be True or False")

        return self._convert(value)

    def _convert(self, value):
        if isinstance(value, self._convertable):
            if isinstance(value, string_types):
                value = value.strip().lower()

            if value in self._aliases_true:
                return True

            if value in self._aliases_false:
                return False

        raise DataError("value cannot be converted to bool")

    def repr(self, memo):
        if not self.convert:
            return "<{0}>".format(self.__class__.__name__)

        return "<{0}(convert)>".format(self.__class__.__name__)


@implements_metaclass
class NumberMeta(ValidatorMeta):

    """
    Allows slicing syntax for min and max arguments for number validators.

    >>> Int[1:]
    <Int(gte=1)>
    >>> Int[1:10]
    <Int(gte=1, lte=10)>
    >>> Int[:10]
    <Int(lte=10)>
    >>> Float[1:]
    <Float(gte=1)>
    >>> Int > 3
    <Int(gt=3)>
    >>> 1 < (Float < 10)
    <Float(gt=1, lt=10)>
    >>> (Int > 5).check(10)
    10
    >>> extract_error(Int > 5, 1)
    'value should be greater than 5'
    >>> (Int < 3).check(1)
    1
    >>> extract_error(Int < 3, 3)
    'value should be less than 3'
    """

    def __getitem__(cls, value):
        if not isinstance(value, slice):
            raise ValueError("slice expected, got {0}".format(value.__class__))

        return cls(gte=value.start, lte=value.stop)

    def __lt__(cls, value):
        return cls(lt=value)

    def __gt__(cls, value):
        return cls(gt=value)


class NumberBase(metaclass(NumberMeta), TypeConvert):

    """
    Base class for Float and Int.
    """

    _convertable = string_types + (numbers.Real, )

    def __init__(self, gte=None, lte=None, gt=None, lt=None):
        super(NumberBase, self).__init__()

        self.gte = gte
        self.lte = lte
        self.gt = gt
        self.lt = lt

    def _check(self, value):
        value = self._convert(value)

        if self.gte is not None and value < self.gte:
            raise DataError("value is less than {0}".format(self.gte))

        if self.lte is not None and value > self.lte:
            raise DataError("value is greater than {0}".format(self.lte))

        if self.lt is not None and value >= self.lt:
            raise DataError("value should be less than {0}".format(self.lt))

        if self.gt is not None and value <= self.gt:
            raise DataError("value should be greater than {0}".format(self.gt))

        return value

    def __lt__(self, lt):
        return self.__class__(gte=self.gte, lte=self.lte, gt=self.gt, lt=lt)

    def __gt__(self, gt):
        return self.__class__(gte=self.gte, lte=self.lte, gt=gt, lt=self.lt)

    def repr(self, memo):
        options = []

        for name in ("gte", "lte", "gt", "lt"):
            value = getattr(self, name)

            if value is not None:
                options.append("{0}={1}".format(name, value))

        if not options:
            return "<{0}>".format(self.__class__.__name__)

        return "<{0}>({1})".format(self.__class__.__name__, ", ".join(options))


class Float(NumberBase):

    """
    >>> Float()
    <Float>
    >>> Float(gte=1)
    <Float(gte=1)>
    >>> Float(lte=10)
    <Float(lte=10)>
    >>> Float(gte=1, lte=10)
    <Float(gte=1, lte=10)>
    >>> Float().check(1.0)
    1.0
    >>> extract_error(Float(), 1 + 3j)
    'value is not float'
    >>> extract_error(Float(), 1)
    1.0
    >>> Float(gte=2).check(3.0)
    3.0
    >>> extract_error(Float(gte=2), 1.0)
    'value is less than 2'
    >>> Float(lte=10).check(5.0)
    5.0
    >>> extract_error(Float(lte=3), 5.0)
    'value is greater than 3'
    >>> Float().check("5.0")
    5.0
    """

    _value_type = float


class Int(NumberBase):

    """
    >>> Int()
    <Int>
    >>> Int().check(5)
    5
    >>> extract_error(Int(), 1.1)
    'value is not int'
    >>> extract_error(Int(), 1 + 1j)
    'value is not int'
    """

    _value_type = int

    def _convert(self, value):
        if isinstance(value, self._value_type):
            return value

        if not isinstance(value, self._convertable):
            raise self._cannot_convert()

        try:
            value = float(value)
        except ValueError:
            raise self._cannot_convert()

        if not value.is_integer():
            raise DataError("value is not int")

        return int(value)


class Atom(ValidatorBase):

    """
    >>> Atom("atom").check("atom")
    'atom'
    >>> extract_error(Atom("atom"), "molecule")
    "value is not exactly 'atom'"
    """

    def __init__(self, value):
        super(Atom, self).__init__()

        self.value = value

    def _check(self, value):
        if self.value != value:
            raise DataError("value is not exactly {0!r}".format(self.value))

        return self.value


class String(ValidatorBase):

    r"""
    >>> String()
    <String>
    >>> String().check("foo")
    'foo'
    >>> String().check("")
    ''
    >>> extract_error(String(), 1)
    'value is not a string'
    >>> String(regex=r"\w+").check("wqerwqer")
    'wqerwqer'
    >>> extract_error(String(regex=r"^\w+$"), "wqe rwqer")
    'value does not match pattern'
    """

    _re_compiled_type = re.compile(r"").__class__

    def __init__(self, regex=None, flags=0):
        super(String, self).__init__()

        self.regex = None

        if isinstance(regex, self._re_compiled_type):
            self.regex = regex

        elif isinstance(regex, string_types):
            self.regex = re.compile(regex, flags)

    def _check(self, value):
        if not isinstance(value, string_types):
            raise DataError("value is not a string")

        if self.regex is not None:
            match = self.regex.match(value)

            if not match:
                raise DataError("value does not match pattern")

            return match

        return value

    def _converter_default(self, value):
        if self.regex is not None:
            return value.group()

        return value

    def __deepcopy__(self, memo):
        # workaround for http://bugs.python.org/issue10076
        memo[id(self)] = self

        copied_dict = {}

        for key, value in iteritems(self.__dict__):
            if isinstance(value, self._re_compiled_type):
                copied_dict[key] = value
            else:
                copied_dict[key] = copy.deepcopy(value, memo)

        obj = self.__class__()
        obj.__dict__.clear()
        obj.__dict__.update(copied_dict)

        return obj

    def repr(self, memo):
        if self.regex:
            return "<{0}(<regex>)>".format(self.__class__.__name__)

        return "<{0}>".format(self.__class__.__name__)


@implements_metaclass
class SquareBracketsMeta(ValidatorMeta):

    """
    Allows usage of square brackets for List initialization

    >>> List[Int]
    <List(<Int>)>
    >>> List[Int, 1:]
    <List(min_length=1 | <Int>)>
    >>> List[:10, Int]
    <List(max_length=10 | <Int>)>
    >>> List[1:10]
    Traceback (most recent call last):
    ...
    RuntimeError: Validator is required for List initialization
    """

    def __getitem__(cls, args):
        min_length = 0
        max_length = None
        validator = None

        if not isinstance(args, tuple):
            args = (args, )

        for arg in args:
            if isinstance(arg, slice):
                if arg.start is not None:
                    min_length = arg.start

                if arg.stop is not None:
                    max_length = arg.stop

            else:
                validator = arg

        if validator is None:
            raise RuntimeError("Validator is required for List initialization")

        return cls(validator, min_length=min_length, max_length=max_length)


class List(metaclass(SquareBracketsMeta), ValidatorBase):

    """
    >>> List(Int)
    <List(<Int>)>
    >>> List(Int, min_length=1)
    <List(min_length=1 | <Int>)>
    >>> List(Int, min_length=1, max_length=10)
    <List(min_length=1, max_length=10 | <Int>)>
    >>> extract_error(List(Int), 1)
    'value is not list'
    >>> List(Int).check([1, 2, 3])
    [1, 2, 3]
    >>> List(String).check(["foo", "bar", "spam"])
    ['foo', 'bar', 'spam']
    >>> extract_error(List(Int), [1, 2, 1 + 3j])
    {2: 'value is not int'}
    >>> List(Int, min_length=1).check([1, 2, 3])
    [1, 2, 3]
    >>> extract_error(List(Int, min_length=1), [])
    'list length is less than 1'
    >>> List(Int, max_length=2).check([1, 2])
    [1, 2]
    >>> extract_error(List(Int, max_length=2), [1, 2, 3])
    'list length is greater than 2'
    >>> extract_error(List(Int), ["a"])
    {0: 'value cannot be converted to int'}
    """

    def __init__(self, validator, min_length=0, max_length=None):
        super(List, self).__init__()

        self.validator = self._ensure_validator(validator)
        self.min_length = min_length
        self.max_length = max_length

    def _check(self, value):
        if not isinstance(value, list):
            raise DataError("value is not list")

        if len(value) < self.min_length:
            raise DataError("list length is less than {0}".format(self.min_length))

        if self.max_length is not None and len(value) > self.max_length:
            raise DataError("list length is greater than {0}".format(self.max_length))

        result = []
        errors = {}

        for index, item in enumerate(value):
            try:
                result.append(self.validator.check(item))
            except DataError as err:
                errors[index] = err

        if errors:
            raise DataError(errors)

        return result

    def repr(self, memo):
        options = []

        if self.min_length:
            options.append("min_length={0}".format(self.min_length))

        if self.max_length:
            options.append("max_length={0}".format(self.max_length))

        return "<{0}({1}{2}{3})>".format(self.__class__.__name__, ", ".join(options),
                                         " | " if options else "", self.validator.repr(memo))


class Tuple(ValidatorBase):
    """
    Tuple checker can be used to check fixed tuples, like (Int, Int, String).

    >>> t = Tuple(Int, Int, String)
    >>> t.check([3, 4, '5'])
    (3, 4, '5')
    >>> extract_error(t, [3, 4, 5])
    {2: 'value is not a string'}
    >>> t
    <Tuple(<Int>, <Int>, <String>)
    """

    def __init__(self, *args):
        super(Tuple, self).__init__()

        self.validators = tuple(map(self._ensure_validator, args))

    def _check(self, value):
        try:
            value = tuple(value)
        except TypeError:
            raise DataError("value must be convertable to tuple")

        length = len(self.validators)

        if len(value) != length:
            raise DataError("value must contain exact {0} items".format(length))

        result = []
        errors = {}

        for idx, (item, validator) in enumerate(zip(value, self.validators)):
            try:
                result.append(validator.check(item))
            except DataError as err:
                errors[idx] = err

        if errors:
            raise DataError(errors)

        return tuple(result)

    def repr(self, memo):
        return "<{0}({1})>".format(
            self.__class__.__name__,
            ", ".join(validator.repr(memo) for validator in self.validators),
        )


class Key(object):

    """
    Helper class for Dict.
    """

    def __init__(self, name, default=Undefined, optional=False, to_name=None, validator=None):
        super(Key, self).__init__()

        self.name = name
        self.to_name = to_name
        self.default = default
        self.optional = optional
        self.validator = validator or Any()

    def pop(self, data):
        if self.name in data:
            yield (self._get_name(), catch_error(self.validator, data.pop(self.name)))
            raise StopIteration()

        if self.optional:
            raise StopIteration()

        default = self.default

        if default is not Undefined:
            if callable(default):
                default = default()

            yield (self._get_name(), catch_error(self.validator, default))
            raise StopIteration()

        yield (self.name, DataError("is required"))

    def _get_name(self):
        return self.to_name or self.name

    def keys_names(self):
        yield self.name

    def __rshift__(self, name):
        key = copy.deepcopy(self)
        key.to_name = name
        return key

    def __cmp__(self, other):
        return cmp(self.name, other.name)

    def __str__(self):
        return "{0}={1}".format(self.name, self.validator)

    def __repr__(self):
        if not self.to_name:
            return "<{0}({1!r})>".format(self.__class__.__name__, self.name)

        return "<{0}({1!r} to {2!r})>".format(self.__class__.__name__, self.name, self.to_name)


class Dict(ValidatorBase):

    """
    >>> validator = Dict(foo=Int, bar=String)
    >>> validator.check({"foo": 1, "bar": "spam"})
    {'foo': 1, 'bar': 'spam'}
    >>> extract_error(validator, {"foo": 1, "bar": 2})
    {'bar': 'value is not a string'}
    >>> extract_error(validator, {"foo": 1})
    {'bar': 'is required'}
    >>> extract_error(validator, {"foo": 1, "bar": "spam", "eggs": None})
    {'eggs': "'eggs' is not allowed key"}
    >>> validator = Dict({Key('bar', default='nyanya') >> 'baz': String}, foo=Int)
    >>> validator.check({'foo': 4})
    {'foo': 4, 'baz': 'nyanya'}
    >>> validator = Dict({String: Int | Bool, Int: String})
    >>> validator
    <Dict(<Int>=<String>, <String>=<Or(<Int>, <Bool>)>)>
    >>> validator.check({"foo": 3, "bar": False})
    {'foo': 3, 'bar': 0}
    >>> validator.check({"foo": 3, 15: "bar"})
    {'foo': 3, 15: 'bar'}
    >>> extract_error(validator, {"foo": 3, 15: "bar", "baz": "spam"})
    {'baz': {'<Mapping(<Int> => <String>)>': {'key': 'value cannot be converted to int'}, \
        '<Mapping(<String> => <Or(<Int>, <Bool>)>)>': {'value': \
        {'<Bool>': 'value should be True or False', '<Int>': \
        'value cannot be converted to int'}}}}
    """

    def __init__(self, *args, **kwargs):
        super(Dict, self).__init__()

        self._hard_keys = []
        self._soft_keys = []

        validators = {}

        for arg in args:
            validators.update(dict(arg))

        validators.update(kwargs)

        for key, validator in iteritems(validators):
            if isinstance(key, ValidatorBase) or \
                    (isinstance(key, class_types) and issubclass(key, ValidatorBase)):
                self._soft_keys.append(Mapping(key, validator))

            else:
                if not isinstance(key, Key):
                    key = Key(key)

                key.validator = self._ensure_validator(validator)
                self._hard_keys.append(key)

    def make_optional(self, *args):
        for key in self._hard_keys:
            if not args or key.name in args:
                key.optional = True

        return self

    def _check(self, value):
        if not isinstance(value, dict):
            raise DataError("value is not dict")

        data = copy.copy(value)
        collect = {}
        errors = {}

        for key in self._hard_keys:
            for k, v in key.pop(data):
                if isinstance(v, DataError):
                    errors[k] = v
                else:
                    collect[k] = v

        if self._soft_keys:
            for k, v in iteritems(data):
                item_errors = {}

                for validator in self._soft_keys:
                    try:
                        checked_mapping = validator.check({k: v})
                    except DataError as e:
                        item_errors.setdefault(repr(validator), []).append(e.error[k])
                    else:
                        k, v = next(iteritems(checked_mapping))
                        collect[k] = v
                        break

                else:
                    for sncl_repr, err_lst in iteritems(item_errors):
                        if len(err_lst) == 1:
                            item_errors[sncl_repr] = err_lst[0]
                        else:
                            item_errors[sncl_repr] = DataError(dict(enumerate(err_lst)))

                    errors[k] = DataError(item_errors)

        else:
            for key in data:
                errors[key] = DataError("{0!r} is not allowed key".format(key))

        if errors:
            raise DataError(errors)

        return collect

    def keys_names(self):
        for key in self._hard_keys:
            for k in key.keys_names():
                yield k

    def repr(self, memo):
        keys = []

        for key in sorted(self._hard_keys):
            keys.append("{0}={1}".format(key.name, key.validator.repr(memo)))

        for validator in self._soft_keys:
            keys.append("{0}={1}".format(validator.validator_key.repr(memo),
                                         validator.validator_value.repr(memo)))

        return "<{0}({1})>".format(self.__class__.__name__, ", ".join(keys))


class Mapping(ValidatorBase):

    """
    >>> validator = Mapping(String, Int)
    >>> validator
    <Mapping(<String> => <Int>)>
    >>> validator.check({"foo": 1, "bar": 2})
    {'foo': 1, 'bar': 2}
    >>> extract_error(validator, {"foo": 1, "bar": None})
    {'bar': {'value': 'value is not int'}}
    >>> extract_error(validator, {"foo": 1, 2: "bar"})
    {2: {'key': 'value is not a string', 'value': 'value cannot be converted to int'}}
    """

    def __init__(self, key, value):
        super(Mapping, self).__init__()

        self.validator_key = self._ensure_validator(key)
        self.validator_value = self._ensure_validator(value)

    def _check(self, mapping):
        checked_mapping = {}
        errors = {}

        for key, value in iteritems(mapping):
            pair_errors = {}

            try:
                checked_key = self.validator_key.check(key)
            except DataError as err:
                pair_errors["key"] = err

            try:
                checked_value = self.validator_value.check(value)
            except DataError as err:
                pair_errors["value"] = err

            if pair_errors:
                errors[key] = DataError(pair_errors)
            else:
                checked_mapping[checked_key] = checked_value

        if errors:
            raise DataError(errors)

        return checked_mapping

    def repr(self, memo):
        return "<{0}({1} => {2})>".format(
            self.__class__.__name__,
            self.validator_key.repr(memo),
            self.validator_value.repr(memo),
        )


class Enum(ValidatorBase):

    """
    >>> validator = Enum("foo", "bar", 1)
    >>> validator
    <Enum('foo', 'bar', 1)>
    >>> validator.check("foo")
    'foo'
    >>> validator.check(1)
    1
    >>> extract_error(validator, 2)
    'value does not match any variant'
    """

    def __init__(self, *args):
        super(Enum, self).__init__()

        self.variants = args

    def _check(self, value):
        if value not in self.variants:
            raise DataError("value does not match any variant")

        return value

    def repr(self, memo):
        return "<{0}({1})>".format(self.__class__.__name__, ", ".join(map(repr, self.variants)))


class Callable(ValidatorBase):

    """
    >>> Callable().check(lambda: 1)
    <function <lambda> at 0xdbe758>
    >>> extract_error(Callable(), 1)
    'value is not callable'
    """

    def _check(self, value):
        if not callable(value):
            raise DataError("value is not callable")

        return value


class Call(ValidatorBase):

    """
    >>> def validator(value):
    ...     if value != "foo":
    ...         raise DataError("I want only foo!")
    ...     return "foo"
    ...
    >>> validator = Call(validator)
    >>> validator
    <Call(validator)>
    >>> validator.check("foo")
    'foo'
    >>> extract_error(validator, "bar")
    'I want only foo!'
    """

    def __init__(self, function):
        super(Call, self).__init__()

        if not callable(function):
            raise RuntimeError("Call argument should be callable")

        self.function = function

    def _check(self, value):
        return self.function(value)

    def repr(self, memo):
        return "<{0}({1})>".format(
            self.__class__.__name__,
            getattr(self.function, "__name__", "<unnamed>"),
        )


class Forward(ValidatorBase):

    """
    >>> node = Forward()
    >>> node << Dict(name=String, children=List[node])
    >>> node
    <Forward(<Dict(children=<List(<recur>)>, name=<String>)>)>
    >>> node.check({"name": "foo", "children": []}) == {'children': [], 'name': 'foo'}
    True
    >>> extract_error(node, {"name": "foo", "children": [1]})
    {'children': {0: 'value is not dict'}}
    >>> node.check({"name": "foo", "children": [{"name": "bar", "children": []} ]}) == \\
    ... {'children': [{'children': [], 'name': 'bar'}], 'name': 'foo'}
    True
    """

    def __init__(self):
        super(Forward, self).__init__()

        self.validator = None

    def __lshift__(self, validator):
        self.provide(validator)

    def provide(self, validator):
        if self.validator:
            raise RuntimeError("validator for Forward is already specified")

        self.validator = self._ensure_validator(validator)

    def _check(self, value):
        if self.validator is None:
            raise RuntimeError("validator for Forward is not specified")

        return self.validator.check(value)

    def repr(self, memo):
        if memo.get(id(self)):
            return "<recur>"

        memo[id(self)] = True

        return "<Forward({0})>".format(self.validator.repr(memo))

    def __deepcopy__(self, memo):  # pylint: disable=W0613
        return self


def catch_error(validator, *args, **kwargs):
    """
    Helper for tests - catch error and return it as dict.
    """
    try:
        return validator.check(*args, **kwargs)
    except DataError as error:
        return error


def extract_error(validator, *args, **kwargs):
    """
    Helper for tests - catch error and return it as dict.
    """
    result = catch_error(validator, *args, **kwargs)

    if isinstance(result, DataError):
        return result.as_dict()

    return result
