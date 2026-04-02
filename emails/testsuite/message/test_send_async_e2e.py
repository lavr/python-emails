"""
End-to-end async SMTP tests.

These tests require a running SMTP server (e.g. Mailpit) and are
skipped unless SMTP_TEST_SETS is set in the environment.  They
mirror the sync e2e tests in test_send.py but use
``message.send_async()`` and ``AsyncSMTPBackend``.
"""
from __future__ import annotations

import pytest

import emails
from emails.backend.smtp.aio_backend import AsyncSMTPBackend

from .helpers import common_email_data
from emails.testsuite.smtp_servers import get_servers


@pytest.mark.e2e
@pytest.mark.asyncio
async def test_send_async_simple():
    """send_async(smtp={...}) delivers a message through a real SMTP server."""
    message = emails.html(**common_email_data(subject='Async simple e2e test'))
    for tag, server in get_servers():
        server.patch_message(message)
        response = await message.send_async(smtp=server.params)
        assert response.success


@pytest.mark.e2e
@pytest.mark.asyncio
async def test_send_async_with_backend_object():
    """send_async(smtp=AsyncSMTPBackend(...)) delivers a message."""
    for tag, server in get_servers():
        backend = AsyncSMTPBackend(**server.params)
        try:
            message = emails.html(**common_email_data(subject='Async backend obj e2e'))
            server.patch_message(message)
            response = await message.send_async(smtp=backend)
            assert response.success
        finally:
            await backend.close()


@pytest.mark.e2e
@pytest.mark.asyncio
async def test_send_async_with_context_manager():
    """AsyncSMTPBackend works as an async context manager for multiple sends."""
    for _, server in get_servers():
        async with AsyncSMTPBackend(**server.params) as backend:
            for n in range(2):
                data = common_email_data(subject='async context manager {0}'.format(n))
                message = emails.html(**data)
                server.patch_message(message)
                response = await message.send_async(smtp=backend)
                assert response.success or response.status_code in (421, 451), \
                    'error sending to {0}'.format(server.params)
        assert backend._client is None
