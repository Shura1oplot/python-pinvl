#!/usr/bin/env python3

import sys
import os


def read(*args):
    return open(os.path.join("pinvl", *args)).read().split("\n")


def get_imports(*args):
    def find_imports(lines):
        imports = []

        for line in lines:
            if line.startswith("import ") or line.startswith("from "):
                if line.startswith("import .") or line.startswith("from ."):
                    continue

                if line not in imports:
                    imports.append(line)

        return imports

    imports = []

    for lines in args:
        for line in find_imports(lines):
            if line not in imports:
                imports.append(line)

    return imports


def get_code(lines):
    code = []
    skip = True

    for line in lines:
        if line == "# PORTABLE:CODE":
            skip = False
            continue

        if not skip:
            code.append(line)

    return code


def main(argv=sys.argv):
    init_file = read("__init__.py")
    compat = read("_compat.py")
    validators = read("validators.py")

    code = ["# -*- coding: utf-8 -*-", ""]

    inside_doc = False

    for line in init_file:
        if line == '"""' and not inside_doc:
            inside_doc = True
            code.append(line)
            continue

        if inside_doc:
            code.append(line)

        if line == '"""':
            break

    code.append("")
    code.extend(get_imports(compat, validators))
    code.extend(("", ""))

    for line in init_file:
        if line.startswith("__version__ = ") or line.startswith("__version_info__ = "):
            code.append(line)

    code.extend(("", ""))
    inside_all = False

    for line in validators:
        if line.startswith("__all__ = "):
            inside_all = True

        if inside_all:
            code.append(line)

        if ")" in line:
            break

    code.extend(("", ""))
    code.extend(get_code(compat))
    code.append("")
    code.extend(get_code(validators))

    print("\n".join(code), end="")


if __name__ == "__main__":
    sys.exit(main())
