import logging
import datetime
import pytest
import base64
import time
import random
import sys
import platform
import os
import functools
import threading
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer


logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger()

import cssutils
cssutils.log.setLevel(logging.FATAL)

import emails.utils

TESTSUITE_ROOT = os.path.dirname(__file__)


class _QuietHandler(SimpleHTTPRequestHandler):
    def log_message(self, *args):
        pass


@pytest.fixture(scope='session')
def _http_fixtures_server():
    handler = functools.partial(_QuietHandler, directory=TESTSUITE_ROOT)
    server = ThreadingHTTPServer(('127.0.0.1', 0), handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    yield 'http://127.0.0.1:%s/' % server.server_address[1]
    server.shutdown()
    server.server_close()


@pytest.fixture
def http_fixtures(_http_fixtures_server, monkeypatch):
    """
    Base url of a local HTTP server that serves files from emails/testsuite,
    e.g. http_fixtures + 'data/http/python-logo.gif'.
    Fetching from loopback is allowed while the fixture is active.
    """
    monkeypatch.setattr(emails.utils, 'url_validator', None)
    return _http_fixtures_server


@pytest.fixture(scope='module')
def django_email_backend(request):
    from django.conf import settings
    logger.debug('django_email_backend...')
    settings.configure(EMAIL_BACKEND='django.core.mail.backends.filebased.EmailBackend',
                       EMAIL_FILE_PATH='tmp-emails')
    from django.core.mail import get_connection
    return get_connection()

