from __future__ import annotations

import socket
from unittest.mock import AsyncMock, MagicMock, patch

import aiosmtplib
import pytest
from emails.backend.smtp.aio_backend import AsyncSMTPBackend
from emails.backend.smtp.aio_client import AsyncSMTPClientWithResponse


@pytest.fixture
def mock_msg():
    msg = MagicMock()
    msg.as_bytes.return_value = b"Subject: test\r\n\r\nHello"
    return msg


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
async def test_lifecycle_connect_send_close(mock_smtp, mock_msg):
    """Full lifecycle: get_client -> sendmail -> close."""
    backend = AsyncSMTPBackend(host='localhost', port=2525)

    # get_client creates and initializes the client
    client = await backend.get_client()
    assert client is not None
    assert backend._client is client
    mock_smtp.connect.assert_awaited_once()

    # sendmail sends the message
    response = await backend.sendmail(
        from_addr='a@b.com',
        to_addrs='c@d.com',
        msg=mock_msg,
    )
    assert response is not None
    assert response.success

    # close shuts down the connection
    await backend.close()
    assert backend._client is None
    mock_smtp.quit.assert_awaited_once()


@pytest.mark.asyncio
async def test_get_client_reuses_connection(mock_smtp, mock_msg):
    """get_client returns the same client on subsequent calls."""
    backend = AsyncSMTPBackend(host='localhost', port=2525)
    client1 = await backend.get_client()
    client2 = await backend.get_client()
    assert client1 is client2
    # connect called only once
    mock_smtp.connect.assert_awaited_once()
    await backend.close()


@pytest.mark.asyncio
async def test_get_client_with_login(mock_smtp):
    """get_client logs in when user/password provided."""
    backend = AsyncSMTPBackend(host='localhost', port=2525, user='me', password='secret')
    await backend.get_client()
    mock_smtp.login.assert_awaited_once_with('me', 'secret')
    await backend.close()


@pytest.mark.asyncio
async def test_reconnect_after_disconnect(mock_smtp, mock_msg):
    """After SMTPServerDisconnected during send, backend reconnects and retries."""
    backend = AsyncSMTPBackend(host='localhost', port=2525)

    # First get_client succeeds, first _send raises disconnect, second _send succeeds
    call_count = 0
    original_mail = mock_smtp.mail

    async def mail_side_effect(*args, **kwargs):
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            raise aiosmtplib.SMTPServerDisconnected('gone')
        return MagicMock(code=250, message='OK')

    mock_smtp.mail = AsyncMock(side_effect=mail_side_effect)

    response = await backend.sendmail(
        from_addr='a@b.com',
        to_addrs='c@d.com',
        msg=mock_msg,
    )
    assert response is not None
    assert response.success
    # Should have connected twice (initial + reconnect)
    assert mock_smtp.connect.await_count == 2
    await backend.close()


@pytest.mark.asyncio
async def test_fail_silently_true_on_connect_error(mock_smtp, mock_msg):
    """With fail_silently=True, connection errors return error response without raising."""
    mock_smtp.connect.side_effect = OSError(socket.EAI_NONAME, 'Name not found')

    backend = AsyncSMTPBackend(host='invalid.example', port=2525, fail_silently=True)
    response = await backend.sendmail(
        from_addr='a@b.com',
        to_addrs='c@d.com',
        msg=mock_msg,
    )
    assert response is not None
    assert not response.success
    assert response.error is not None


@pytest.mark.asyncio
async def test_fail_silently_false_raises(mock_smtp, mock_msg):
    """With fail_silently=False, connection errors propagate as exceptions."""
    mock_smtp.connect.side_effect = aiosmtplib.SMTPConnectError('refused')

    backend = AsyncSMTPBackend(host='invalid.example', port=2525, fail_silently=False)
    with pytest.raises(aiosmtplib.SMTPConnectError):
        await backend.sendmail(
            from_addr='a@b.com',
            to_addrs='c@d.com',
            msg=mock_msg,
        )


@pytest.mark.asyncio
async def test_empty_to_addrs_returns_none(mock_msg):
    """sendmail with empty to_addrs returns None."""
    backend = AsyncSMTPBackend(host='localhost', port=2525)
    response = await backend.sendmail(
        from_addr='a@b.com',
        to_addrs=[],
        msg=mock_msg,
    )
    assert response is None


@pytest.mark.asyncio
async def test_ssl_tls_mutually_exclusive():
    """Cannot set both ssl and tls."""
    with pytest.raises(ValueError):
        AsyncSMTPBackend(host='localhost', port=465, ssl=True, tls=True)


@pytest.mark.asyncio
async def test_context_manager(mock_smtp, mock_msg):
    """AsyncSMTPBackend works as an async context manager."""
    async with AsyncSMTPBackend(host='localhost', port=2525) as backend:
        client = await backend.get_client()
        assert client is not None
    # after exiting, client should be None
    assert backend._client is None


@pytest.mark.asyncio
async def test_close_clears_client_on_error(mock_smtp):
    """close() clears the client even if quit raises (when fail_silently=True)."""
    mock_smtp.quit.side_effect = aiosmtplib.SMTPServerDisconnected('already gone')

    backend = AsyncSMTPBackend(host='localhost', port=2525, fail_silently=True)
    await backend.get_client()
    assert backend._client is not None

    await backend.close()
    assert backend._client is None


@pytest.mark.asyncio
async def test_string_to_addrs_converted_to_list(mock_smtp, mock_msg):
    """A single string to_addrs is converted to a list."""
    backend = AsyncSMTPBackend(host='localhost', port=2525)
    response = await backend.sendmail(
        from_addr='a@b.com',
        to_addrs='c@d.com',
        msg=mock_msg,
    )
    assert response is not None
    assert response.success
    await backend.close()


@pytest.mark.asyncio
async def test_mail_options_passed_through(mock_smtp, mock_msg):
    """mail_options from constructor are used if not overridden in sendmail."""
    backend = AsyncSMTPBackend(host='localhost', port=2525, mail_options=['BODY=8BITMIME'])
    response = await backend.sendmail(
        from_addr='a@b.com',
        to_addrs='c@d.com',
        msg=mock_msg,
    )
    assert response is not None
    assert response.success
    # Verify BODY=8BITMIME was passed to the SMTP mail command
    mail_call_args = mock_smtp.mail.call_args
    assert 'BODY=8BITMIME' in mail_call_args.kwargs.get('options', [])
    await backend.close()
