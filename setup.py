from setuptools import setup
import os.path
import io


def read(filename, encoding="utf-8"):
    return io.open(os.path.join(os.path.dirname(__file__), filename),
                   encoding=encoding).read()


setup(
    name="pinvl",
    version="0.1.0",
    license="BSD",
    description="Pinvl is validation library with support to convert data structures",
    long_description=read("README.rst"),
    author="Barbuza, Deepwalker, nimnull, Shura1oplot",
    author_email="s0meuser@yandex.ru",
    url="https://github.com/Shura1oplot/python-pinvl/",
    packages=("pinvl", "pinvl.contrib"),
    classifiers=(
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: BSD License",
        "Programming Language :: Python",
        "Programming Language :: Python :: 2",
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.2",
        "Programming Language :: Python :: 3.3",
        "Programming Language :: Python :: 3.4",
        "Operating System :: OS Independent",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Internet :: WWW/HTTP :: Dynamic Content :: CGI Tools/Libraries",
    ),
    keywords=("validatation", "form", "forms", "data", "schema"),
    extras_require=dict(
        rfc3339=("python-dateutil>=1.5", ),
        objectid=("pymongo>=2.0.0", ),
    ),
    entry_points=dict(
        pinvl=(
            ".URL = pinvl.contrib.url:URL",
            ".Email = pinvl.contrib.email:Email",
            ".DateTime = pinvl.contrib.rfc_3339:DateTime [rfc3339]",
            ".MongoId = pinvl.contrib.object_id:MongoId [objectid]",
        ),
    ),
)
