#!/usr/bin/python3

from setuptools import setup, find_packages
setup(
    name = "mistest",
    version = "0.1",
    packages = ['mistest'],

    entry_points = {
        'console_scripts': [
            'mistest = mistest:main'
        ]
    },

    # Project uses reStructuredText, so ensure that the docutils get
    # installed or upgraded on the target machine
    install_requires = ['ply >= 3.4'],

    # metadata for upload to PyPI
    author = "Nils Carlson",
    author_email = "pyssling@ludd.ltu.se",
    description = "A test harness for parsing TAP and executing tests in parallel",
    license = "GPLv3",
    keywords = "tap harness test parallel",
    url = "http://github.com/pyssling/mistest/",
)
