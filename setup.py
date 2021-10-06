# -*- coding: utf-8 -*-

# Learn more: https://confluence.securepassage.com/display/DEVNETSEC/FMAPI%3A+Python+Firemon+API+module

from setuptools import setup, find_packages
from distutils.util import convert_path

PROJECT = "firemon-api"

setup(
    name=PROJECT,
    use_scm_version=True,
    setup_requires=["setuptools_scm"],
    description="NetSec Python Wrapper for Firemon API",
    author="Firemon NetSec <dev-netsec@firemon.com>",
    author_email="dev-netsec@firemon.com",
    url="https://www.firemon.com/",
    project_urls={
        "Repository": "https://stash.securepassage.com/scm/nsu/firemon-api",
        "Documentation": "https://confluence.securepassage.com/display/DEVNETSEC/FMAPI%3A+Python+Firemon+API+module",
    },
    packages=find_packages(exclude=("tests", "docs")),
    include_package_data=True,
    python_requires=">=3.8",
    install_requires=[
        "requests",
        "setuptools_scm>=6.2",
    ],
    zip_safe=False,
)
