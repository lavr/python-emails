"""Setup configuration for python-emails."""

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


def read_file(filename):
    file_path = os.path.join(os.path.dirname(__file__), filename)
    with codecs.open(file_path, encoding='utf-8') as fh:
        return fh.read()


settings.update(
    name='emails',
    version=find_version('emails/__init__.py'),
    description='Modern python library for emails.',
    long_description=read_file('README.rst'),
    long_description_content_type='text/x-rst',
    author='Sergey Lavrinenko',
    author_email='s@lavr.me',
    url='https://github.com/lavr/python-emails',
    packages=['emails',
              'emails.django',
              'emails.loader',
              'emails.store',
              'emails.backend',
              'emails.backend.smtp',
              'emails.backend.inmemory',
              'emails.template',
             ],
    package_data={'emails': ['py.typed']},
    scripts=['scripts/make_rfc822.py'],
    python_requires='>=3.10',
    install_requires=['python-dateutil', 'puremagic', 'dkimpy'],
    extras_require={
        'html': ['cssutils', 'lxml', 'chardet', 'requests', 'premailer'],
        'jinja': ['jinja2'],
        'async': ['aiosmtplib'],
    },
    zip_safe=False,
    classifiers=(
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Developers',
        'Natural Language :: English',
        "Operating System :: OS Independent",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Programming Language :: Python :: 3.13",
        "Programming Language :: Python :: 3.14",
        "Topic :: Communications",
        "Topic :: Internet :: WWW/HTTP",
        "Topic :: Other/Nonlisted Topic",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ),
    cmdclass={'audit': run_audit}
)


setup(**settings)
