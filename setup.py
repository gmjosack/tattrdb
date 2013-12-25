#!/usr/bin/env python

from distutils.core import setup

execfile('tattrdb/version.py')

with open('requirements.txt') as requirements:
    required = requirements.read().splitlines()

kwargs = {
    "name": "tattrdb",
    "version": str(__version__),
    "packages": ["tattrdb"],
    "scripts": ["bin/tattr"],
    "description": "Tag and Attribute Database.",
    # PyPi, despite not parsing markdown, will prefer the README.md to the
    # standard README. Explicitly read it here.
    "long_description": open("README").read(),
    "author": "Gary M. Josack",
    "maintainer": "Gary M. Josack",
    "author_email": "gary@byoteki.com",
    "maintainer_email": "gary@byoteki.com",
    "license": "MIT",
    "install_requires": required,
    "url": "https://github.com/gmjosack/tattrdb",
    "download_url": "https://github.com/gmjosack/tattrdb/archive/master.tar.gz",
    "classifiers": [
        "Programming Language :: Python",
        "Topic :: Software Development",
        "Topic :: Software Development :: Libraries",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ]
}

setup(**kwargs)
