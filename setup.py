#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys


try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

settings = dict()

# Publish Helper.
if sys.argv[-1] == 'publish':
    os.system('python setup.py sdist upload')
    sys.exit()

settings.update(
    name='emails',
    version='0.1.8',
    description='Missed simple email library for python',
    long_description=open('README.rst').read(),
    author='Sergey Lavrinenko',
    author_email='s@lavr.me',
    url='https://github.com/lavr/python-emails',
    packages = ['emails', 'emails.compat', 'emails.loader', 'emails.store', 'emails.template'],
    scripts=[ ],
    install_requires = [ open('requirements.txt').read().strip().split('\n') ],
    #install_requires = ['cssselect','cssutils','lxml','chardet','python-dateutil','requests','jinja2','mako', 'pydkim'],
    license=open('LICENSE').read(),
    #test_suite = "emails.testsuite.test_all",
    zip_safe=False,
    classifiers=(
        #'Development Status :: 4 - Beta',
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'Natural Language :: English',
        'License :: OSI Approved :: BSD License',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
    )
)


setup(**settings)
