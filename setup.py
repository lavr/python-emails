#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
python-emails
~~~~~~~~~~~~~

Modern python library for email.

Build message:

   >>> import emails
   >>> message = emails.html(html="<p>Hi!<br>Here is your receipt...",
                          subject="Your receipt No. 567098123",
                          mail_from=('Some Store', 'store@somestore.com'))
   >>> message.attach(data=open('bill.pdf'), filename='bill.pdf')

send message and get response from smtp server:

   >>> r = message.send(to='s@lavr.me', smtp={'host': 'aspmx.l.google.com', 'timeout': 5})
   >>> assert r.status_code == 250

and more:

 * DKIM signature
 * Render body from template
 * Flask extension and Django integration
 * Message body transformation methods
 * Load message from url or from file


Links
`````

* `documentation <http://python-emails.readthedocs.org/>`_
* `source code <http://github.com/lavr/python-emails>`_

"""

import codecs
import os
import re
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

def find_version(*file_paths):
    version_file_path = os.path.join(os.path.dirname(__file__),
                                     *file_paths)
    version_file = codecs.open(version_file_path,
                               encoding='utf-8').read()
    version_match = re.search(r"^__version__ = ['\"]([^'\"]*)['\"]",
                              version_file, re.M)
    if version_match:
        return version_match.group(1)
    raise RuntimeError("Unable to find version string.")


settings.update(
    name='emails',
    version=find_version('emails/__init__.py'),
    description='Modern python library for emails.',
    long_description=__doc__,
    long_description_content_type='text/markdown',
    author='Sergey Lavrinenko',
    author_email='s@lavr.me',
    url='https://github.com/lavr/python-emails',
    packages=['emails',
              'emails.compat',
              'emails.django',
              'emails.loader',
              'emails.store',
              'emails.backend',
              'emails.backend.smtp',
              'emails.template',
              'emails.packages',
              'emails.packages.dkim'
             ],
    scripts=['scripts/make_rfc822.py'],
    install_requires=['cssutils', 'lxml', 'chardet', 'python-dateutil', 'requests', 'premailer'],
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
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3.6",
        "Topic :: Communications",
        "Topic :: Internet :: WWW/HTTP",
        "Topic :: Other/Nonlisted Topic",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ),
    cmdclass={'audit': run_audit}
)


setup(**settings)
