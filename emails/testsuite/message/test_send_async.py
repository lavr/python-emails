from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

import emails
from emails.backend.smtp.aio_backend import AsyncSMTPBackend

from .helpers import common_email_data


@pytest.fixture
def mock_smtp():
    """Patch aiosmtplib.SMTP so no real connection is made."""
    with patch('emails.backend.smtp.aio_client.aiosmtplib.SMTP') as mock_cls:
        instance = MagicMock()
        instance.connect = AsyncMock()
        instance.ehlo = AsyncMock()
        instance.helo = AsyncMock()
        instance._ehlo_or_helo_if_needed = AsyncMock()
        instance.login = AsyncMock()
        instance.quit = AsyncMock()
        instance.close = MagicMock()
        instance.mail = AsyncMock(return_value=MagicMock(code=250, message='OK'))
        instance.rcpt = AsyncMock(return_value=MagicMock(code=250, message='OK'))
        instance.data = AsyncMock(return_value=MagicMock(code=250, message='OK'))
        instance.rset = AsyncMock()
        instance.is_ehlo_or_helo_needed = True
        instance.supports_esmtp = True
        instance.supports_extension = MagicMock(return_value=False)
        mock_cls.return_value = instance
        yield instance


@pytest.mark.asyncio
async def test_send_async_with_dict(mock_smtp):
    """send_async(smtp={...}) creates backend, sends, and closes."""
    msg = emails.html(**common_email_data(subject='Async dict test'))
    response = await msg.send_async(smtp={'host': 'localhost', 'port': 2525})
    assert response is not None
    assert response.success
    # Backend should have been closed (quit called)
    mock_smtp.quit.assert_awaited_once()


@pytest.mark.asyncio
async def test_send_async_with_backend_object(mock_smtp):
    """send_async(smtp=AsyncSMTPBackend(...)) uses the provided backend."""
    msg = emails.html(**common_email_data(subject='Async backend test'))
    backend = AsyncSMTPBackend(host='localhost', port=2525)
    response = await msg.send_async(smtp=backend)
    assert response is not None
    assert response.success
    # Backend should NOT have been closed (caller manages lifecycle)
    mock_smtp.quit.assert_not_awaited()
    # Clean up
    await backend.close()


@pytest.mark.asyncio
async def test_send_async_with_default_smtp(mock_smtp):
    """send_async() without smtp uses default localhost:25."""
    msg = emails.html(**common_email_data(subject='Async default test'))
    response = await msg.send_async()
    assert response is not None
    assert response.success


def test_sync_send_unchanged():
    """message.send() still works the sync path (uses SMTPBackend, not async)."""
    msg = emails.html(**common_email_data(subject='Sync unchanged test'))

    mock_backend = MagicMock()
    mock_response = MagicMock(success=True)
    mock_backend.sendmail.return_value = mock_response

    response = msg.send(smtp=mock_backend)
    assert response is mock_response
    assert response.success
    mock_backend.sendmail.assert_called_once()


@pytest.mark.asyncio
async def test_send_async_with_render(mock_smtp):
    """send_async() applies render data before sending."""
    msg = emails.html(**common_email_data(subject='Render test'))
    response = await msg.send_async(
        smtp={'host': 'localhost', 'port': 2525},
        render={'name': 'World'},
    )
    assert response is not None
    assert response.success


@pytest.mark.asyncio
async def test_send_async_with_to_override(mock_smtp):
    """send_async(to=...) overrides mail_to."""
    msg = emails.html(**common_email_data(subject='To override'))
    response = await msg.send_async(
        to='other@example.com',
        smtp={'host': 'localhost', 'port': 2525},
    )
    assert response is not None
    assert response.success
    # Verify the override address was used as recipient
    assert 'other@example.com' in response.to_addrs


@pytest.mark.asyncio
async def test_send_async_invalid_smtp_type():
    """send_async() raises ValueError for invalid smtp type."""
    msg = emails.html(**common_email_data(subject='Invalid smtp'))
    with pytest.raises(ValueError, match="smtp must be a dict"):
        await msg.send_async(smtp=42)


@pytest.mark.asyncio
async def test_send_async_no_from_raises():
    """send_async() raises when no from address."""
    msg = emails.html(
        subject='No from',
        mail_to='to@example.com',
        html='<p>Hello</p>',
    )
    with pytest.raises((ValueError, TypeError)):
        await msg.send_async(smtp={'host': 'localhost', 'port': 2525})


@pytest.mark.asyncio
async def test_send_async_closes_on_error(mock_smtp):
    """send_async(smtp={...}) closes backend even if sendmail fails."""
    mock_smtp.mail.side_effect = Exception('send failed')
    msg = emails.html(**common_email_data(subject='Error close test'))

    with pytest.raises(Exception, match='send failed'):
        await msg.send_async(
            smtp={'host': 'localhost', 'port': 2525, 'fail_silently': False},
        )
    # Backend should still have been closed
    mock_smtp.quit.assert_awaited()
