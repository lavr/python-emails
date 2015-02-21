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

from setuptools import Command, setup

class run_audit(Command):
    """
    By mitsuhiko's code:
    Audits source code using PyFlakes for following issues:
        - Names which are used but not defined or used before they are defined.
        - Names which are redefined without having been used.
    """
    description = "Audit source code with PyFlakes"
    user_options = []

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run(self):
        import os, sys
        try:
            import pyflakes.scripts.pyflakes as flakes
        except ImportError:
            print("Audit requires PyFlakes installed in your system.")
            sys.exit(-1)

        warns = 0
        # Define top-level directories
        dirs = ('emails', 'scripts')
        for dir in dirs:
            for root, _, files in os.walk(dir):
                for file in files:
                    if file != '__init__.py' and file.endswith('.py') :
                        warns += flakes.checkPath(os.path.join(root, file))
        if warns > 0:
            print("Audit finished with total %d warnings." % warns)
        else:
            print("No problems found in sourcecode.")

import emails

settings.update(
    name='emails',
    version=emails.__version__,
    description='Elegant and simple email library for python 2/3',
    long_description=open('README.rst').read(),
    author='Sergey Lavrinenko',
    author_email='s@lavr.me',
    url='https://github.com/lavr/python-emails',
    packages=['emails',
              'emails.compat',
              'emails.loader',
              'emails.store',
              'emails.smtp',
              'emails.template',
              'emails.packages',
              'emails.packages.cssselect',
              'emails.packages.dkim'
             ],
    scripts=['scripts/make_rfc822.py'],
    install_requires=['cssutils', 'lxml', 'chardet', 'python-dateutil', 'requests', 'premailer'],
    license=open('LICENSE').read(),
    #test_suite = "emails.testsuite.test_all",
    zip_safe=False,
    classifiers=(
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'Natural Language :: English',
        'License :: OSI Approved :: BSD License',
        "Operating System :: OS Independent",
        "Programming Language :: Python",
        "Programming Language :: Python :: 2",
        "Programming Language :: Python :: 2.6",
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.3",
        "Programming Language :: Python :: 3.4",
        "Topic :: Communications",
        "Topic :: Internet :: WWW/HTTP",
        "Topic :: Other/Nonlisted Topic",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ),
    cmdclass={'audit': run_audit}
)


setup(**settings)
