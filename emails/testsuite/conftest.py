import logging
import datetime
import pytest
import base64
import time
import random
import sys
import platform


logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger()

import cssutils
cssutils.log.setLevel(logging.FATAL)


@pytest.fixture(scope='module')
def django_email_backend(request):
    from django.conf import settings
    logger.debug('django_email_backend...')
    settings.configure(EMAIL_BACKEND='django.core.mail.backends.filebased.EmailBackend',
                       EMAIL_FILE_PATH='tmp-emails')
    from django.core.mail import get_connection
    return get_connection()

