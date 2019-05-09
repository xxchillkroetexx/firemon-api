# -*- coding: utf-8 -*-

# Learn more: https://www.firemon.com/

from setuptools import setup, find_packages

PROJECT = 'fmapi'

with open('README.rst') as f:
    readme = f.read()

setup(
    name='fmapi',
    version='0.0.2',
    description='NetSec Python Wrapper for Firemon API',
    long_description=readme,
    author='Firemon NetSec <dev-netsec@firemon.com>',
    author_email='dev-netsec@firemon.com',
    url='https://www.firemon.com/',
    project_urls = {
        'Repository': 'https://stash.securepassage.com/projects/NSU/repos/fmapi',
    },
    packages=find_packages(exclude=('tests', 'docs')),
    include_package_data=True,
    install_requires=[
        'requests',
    ],
    zip_safe=False,
)
