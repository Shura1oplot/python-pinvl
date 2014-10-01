# -*- coding: utf-8 -*-

from unittest import TestCase, main
import re
from pinvl import *
from pinvl.validators import extract_error


class PinvlTestCase(TestCase):
    def test_Type(self):
        vdr = Type(int)
        self.assertEqual(vdr.check(1), 1)
        self.assertEqual(extract_error(vdr, 1.0), "value is not int")
        self.assertEqual(extract_error(vdr, "1"), "value is not int")

        class TestClass(object):
            pass

        vdr = Type(TestClass)
        value = TestClass()
        self.assertEqual(vdr.check(value), value)
        self.assertEqual(extract_error(vdr, None), "value is not TestClass")

    def test_Type_meta(self):
        vdr = Type[bool]
        self.assertIsInstance(vdr, Type)
        self.assertEqual(vdr.type, bool)

    def test_Any(self):
        vdr = Any()
        self.assertEqual(vdr.check("foo"), "foo")

    def test_Null(self):
        vdr = Null()
        self.assertEqual(vdr.check(None), None)
        self.assertEqual(extract_error(vdr, 2), "value should be None")

    def test_Bool(self):
        vdr = Bool()
        self.assertEqual(vdr.check(True), True)
        self.assertEqual(vdr.check(False), False)
        self.assertEqual(extract_error(vdr, "foo"), "value should be True or False")

    def test_Bool_convert(self):
        vdr = Bool(convert=True)
        self.assertEqual(vdr.check("true"), True)
        self.assertEqual(vdr.check("n"), False)
        self.assertEqual(extract_error(vdr, "foo"), "value cannot be converted to bool")

    def test_Float(self):
        vdr = Float()
        self.assertEqual(vdr.check(2.7), 2.7)
        self.assertEqual(vdr.check("2.7"), 2.7)
        self.assertEqual(vdr.check(2), 2.0)
        self.assertEqual(vdr.check("2"), 2.0)
        self.assertEqual(extract_error(vdr, "foo"), "value cannot be converted to float")

        vdr = Float(gte=5.2)
        self.assertEqual(extract_error(vdr, 5.1), "value is less than 5.2")
        self.assertEqual(vdr.check(5.2), 5.2)
        self.assertEqual(vdr.check(5.3), 5.3)

        vdr = Float(lte=5.2)
        self.assertEqual(vdr.check(5.1), 5.1)
        self.assertEqual(vdr.check(5.2), 5.2)
        self.assertEqual(extract_error(vdr, 5.3), "value is greater than 5.2")

        vdr = Float(gt=5.2)
        self.assertEqual(extract_error(vdr, 5.1), "value should be greater than 5.2")
        self.assertEqual(extract_error(vdr, 5.2), "value should be greater than 5.2")
        self.assertEqual(vdr.check(5.3), 5.3)

        vdr = Float(lt=5.2)
        self.assertEqual(vdr.check(5.1), 5.1)
        self.assertEqual(extract_error(vdr, 5.2), "value should be less than 5.2")
        self.assertEqual(extract_error(vdr, 5.3), "value should be less than 5.2")

    def test_Int(self):
        vdr = Int()
        self.assertEqual(vdr.check(2), 2)
        self.assertEqual(vdr.check("3"), 3)
        self.assertEqual(extract_error(vdr, 2.1), "value is not int")

    def test_Atom(self):
        vdr = Atom("foo")
        self.assertEqual(vdr.check("foo"), "foo")
        self.assertEqual(extract_error(vdr, "bar"), "value is not exactly 'foo'")

    def test_String(self):
        vdr = String()
        self.assertEqual(vdr.check("foo"), "foo")
        self.assertEqual(extract_error(vdr, 2), "value is not a string")
        self.assertEqual(extract_error(vdr, ""), "")

    def test_String_regex(self):
        vdr = String(regex=r"[a-z]+")
        self.assertEqual(vdr.check("foo"), "foo")
        self.assertEqual(vdr.check("foo bar"), "foo")
        self.assertEqual(extract_error(vdr, "35"), "value does not match pattern")

        vdr = String(regex=r"[a-f]+", flags=re.I)
        self.assertEqual(vdr.check("abcDEF"), "abcDEF")

    def test_Email(self):
        vdr = Email()
        self.assertEqual(vdr.check("someone@example.net"), "someone@example.net")
        self.assertEqual(extract_error(vdr, "foo"), "value is not a valid email address")

    def test_URL(self):
        vdr = URL()
        url = "http://example.net/resource/?param=value#anchor"
        self.assertEqual(vdr.check(url), url)

        url = u"http://пример.рф/resource/?param=value#anchor"
        url_out = u"http://xn--e1afmkfd.xn--p1ai/resource/?param=value#anchor"
        self.assertEqual(vdr.check(url), url_out)

    def test_List(self):
        vdr = List(Int)
        self.assertEqual(vdr.check([1, 2, 3]), [1, 2, 3])
        self.assertEqual(extract_error(vdr, "foo"), "value is not list")

        err = {1: "value cannot be converted to int", 2: "value cannot be converted to int"}
        self.assertEqual(extract_error(vdr, [1, "foo", "bar"]), err)

        vdr = List(Int, min_length=3)
        self.assertEqual(vdr.check([1, 2, 3]), [1, 2, 3])
        self.assertEqual(extract_error(vdr, [1, 2]), "list length is less than 3")

        vdr = List(Int, max_length=3)
        self.assertEqual(vdr.check([1, 2, 3]), [1, 2, 3])
        self.assertEqual(extract_error(vdr, [1, 2, 3, 4]), "list length is greater than 3")

        vdr = List(Int, min_length=3, max_length=5)
        self.assertEqual(vdr.check([1, 2, 3, 4]), [1, 2, 3, 4])
        self.assertEqual(extract_error(vdr, [1, 2]), "list length is less than 3")
        self.assertEqual(extract_error(vdr, [1, 2, 3, 4, 5, 6]), "list length is greater than 5")

    def test_List_meta(self):
        vdr = List[Int]
        self.assertEqual(vdr.check([1, 2, 3]), [1, 2, 3])
        self.assertEqual(extract_error(vdr, "foo"), "value is not list")

        vdr = List[Int, 3:]
        self.assertEqual(vdr.check([1, 2, 3]), [1, 2, 3])
        self.assertEqual(extract_error(vdr, [1, 2]), "list length is less than 3")

        vdr = List[Int, :3]
        self.assertEqual(vdr.check([1, 2, 3]), [1, 2, 3])
        self.assertEqual(extract_error(vdr, [1, 2, 3, 4]), "list length is greater than 3")

        vdr = List[Int, 3:5]
        self.assertEqual(vdr.check([1, 2, 3, 4]), [1, 2, 3, 4])
        self.assertEqual(extract_error(vdr, [1, 2]), "list length is less than 3")
        self.assertEqual(extract_error(vdr, [1, 2, 3, 4, 5, 6]), "list length is greater than 5")

    def test_Tuple(self):
        vdr = Tuple(Int, Int, String)
        self.assertEqual(vdr.check([1, 2, "foo"]), (1, 2, "foo"))
        self.assertEqual(extract_error(vdr, [1, 2, "foo", "bar"]), "value must contain exact 3 items")
        self.assertEqual(extract_error(vdr, [1, 2, 3]), {2: "value is not a string"})

    def test_Dict(self):
        vdr = Dict({
            Key("foo"): Atom("bar"),
        })
        self.assertEqual(vdr.check({"foo": "bar"}), {"foo": "bar"})
        self.assertEqual(extract_error(vdr, {"foo": "spam"}), {"foo": "value is not exactly 'bar'"})
        self.assertEqual(extract_error(vdr, {"foo": "bar", "test": 3}),
                         {"test": "'test' is not allowed key"})

        vdr = Dict(foo=Atom("bar"))
        self.assertEqual(vdr.check({"foo": "bar"}), {"foo": "bar"})

    def test_Dict_optional(self):
        vdr = Dict({
            Key("foo"): Atom("bar"),
            Key("test", optional=True): Int
        })
        self.assertEqual(vdr.check({"foo": "bar"}), {"foo": "bar"})
        self.assertEqual(vdr.check({"foo": "bar", "test": 3}), {"foo": "bar", "test": 3})

    def test_Dict_default(self):
        vdr = Dict({
            Key("foo"): Atom("bar"),
            Key("test", default=1): Int
        })
        self.assertEqual(vdr.check({"foo": "bar"}), {"foo": "bar", "test": 1})
        self.assertEqual(extract_error(vdr, {"foo": "bar", "test": "spam"}),
                         {"test": "value cannot be converted to int"})

        vdr = Dict({
            Key("foo"): Atom("bar"),
            Key("test", default=None): Int | Null
        })
        self.assertEqual(vdr.check({"foo": "bar"}), {"foo": "bar", "test": None})
        self.assertEqual(extract_error(vdr, {"foo": "bar", "test": "spam"}), {
            "test": {
                "<Int>": "value cannot be converted to int",
                "<Null>": "value should be None"
            }
        })

    def test_Dict_to_name(self):
        vdr = Dict({
            Key("foo", to_name="bar"): Int,
        })
        self.assertEqual(vdr.check({"foo": 1}), {"bar": 1})

        vdr = Dict({
            Key("foo") >> "bar": Int,
        })
        self.assertEqual(vdr.check({"foo": 1}), {"bar": 1})

    def test_Dict_vdr_as_key(self):
        vdr = Dict({
            Key("foo"): Atom("bar"),
            String: Int
        })
        self.assertEqual(vdr.check({"foo": "bar"}), {"foo": "bar"})
        self.assertEqual(vdr.check({"foo": "bar", "test": 3}), {"foo": "bar", "test": 3})
        err = {
            "test": {
                "<Mapping(<String> => <Int>)>": {"value": "value cannot be converted to int"}
            }
        }
        self.assertEqual(extract_error(vdr, {"foo": "bar", "test": "spam"}), err)

        vdr = Dict({
            String(regex=r"^\d+$"): Int,
            String(regex=r"^[a-z]+$"): String
        })
        self.assertEqual(vdr.check({"35": 16, "abc": "def"}), {"35": 16, "abc": "def"})
        err = {
            "test": {
                "<Mapping(<String(<regex>)> => <Int>)>":    {"key":   "value does not match pattern"},
                "<Mapping(<String(<regex>)> => <String>)>": {"value": "value is not a string"}
            },
            "35": {
                "<Mapping(<String(<regex>)> => <Int>)>":    {"value": "value cannot be converted to int"},
                "<Mapping(<String(<regex>)> => <String>)>": {"key":   "value does not match pattern"}
            }
        }
        self.assertEqual(extract_error(vdr, {"35": "abc", "test": 16}), err)

    def test_Mapping(self):
        vdr = Mapping(String, Int)
        self.assertEqual(vdr.check({"foo": 1, "bar": 2}), {"foo": 1, "bar": 2})
        self.assertEqual(extract_error(vdr, {"foo": 1, "bar": "spam"}),
                         {"bar": {"value": "value cannot be converted to int"}})

    def test_Enum(self):
        vdr = Enum("foo", 3.14)
        self.assertEqual(vdr.check("foo"), "foo")
        self.assertEqual(vdr.check(3.14), 3.14)
        self.assertEqual(extract_error(vdr, "bar"), "value does not match any variant")

    def test_Callable(self):
        vdr = Callable()
        self.assertEqual(vdr.check(map), map)
        self.assertEqual(extract_error(vdr, None), "value is not callable")

    def test_Call(self):
        vdr = Call(lambda x: x in "abcdef")
        self.assertEqual(vdr.check("a"), True)
        self.assertEqual(vdr.check("z"), False)

    def test_Forward(self):
        vdr = Forward()
        vdr.provide(Dict({
            String: vdr | String
        }))

        data = {
            "foo": {
                "bar": {
                    "baz": "spam"
                }
            }
        }
        self.assertEqual(vdr.check(data), data)

        data = {
            "foo": {
                "bar": {
                    "baz": 15
                }
            }
        }
        self.assertNotEqual(extract_error(vdr, data), data)  # too long error

    def test_Or(self):
        vdr = Int | Float
        self.assertEqual(vdr.check(3), 3)
        self.assertEqual(vdr.check(3.14), 3.14)
        self.assertEqual(extract_error(vdr, "foo"),
                         {"<Int>": "value cannot be converted to int",
                          "<Float>": "value cannot be converted to float"})

        vdr = List(Int) >> sum
        self.assertEqual(vdr.check([1, 2, 3]), 6)


if __name__ == "__main__":
    main()
