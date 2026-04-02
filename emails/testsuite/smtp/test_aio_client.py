from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from emails.backend.response import SMTPResponse


# Helper to build a mock aiosmtplib response
def _aio_resp(code: int = 250, message: str = 'OK'):
    r = MagicMock()
    r.code = code
    r.message = message
    return r


class FakeAsyncSMTPBackend:
    """Minimal stand-in for AsyncSMTPBackend so we can test the client in isolation."""

    response_cls = SMTPResponse

    def make_response(self, exception=None):
        return self.response_cls(backend=self, exception=exception)


@pytest.fixture
def parent():
    return FakeAsyncSMTPBackend()


@pytest.mark.asyncio
async def test_sendmail_success(parent):
    with patch('emails.backend.smtp.aio_client.aiosmtplib') as mock_aio:
        mock_smtp_instance = AsyncMock()
        mock_aio.SMTP.return_value = mock_smtp_instance
        mock_smtp_instance.supports_extension = MagicMock(return_value=False)
        mock_smtp_instance.mail.return_value = _aio_resp(250, 'OK')
        mock_smtp_instance.rcpt.return_value = _aio_resp(250, 'OK')
        mock_smtp_instance.data.return_value = _aio_resp(250, 'OK')

        from emails.backend.smtp.aio_client import AsyncSMTPClientWithResponse
        client = AsyncSMTPClientWithResponse(parent=parent, host='localhost', port=25)
        await client.initialize()

        response = await client.sendmail(
            from_addr='sender@example.com',
            to_addrs=['rcpt@example.com'],
            msg=b'Subject: test\r\n\r\nHello',
        )

        assert response is not None
        assert isinstance(response, SMTPResponse)
        assert response.success
        assert response.status_code == 250
        assert response.from_addr == 'sender@example.com'
        assert response.to_addrs == ['rcpt@example.com']


@pytest.mark.asyncio
async def test_sendmail_empty_to_addrs(parent):
    with patch('emails.backend.smtp.aio_client.aiosmtplib') as mock_aio:
        mock_smtp_instance = AsyncMock()
        mock_aio.SMTP.return_value = mock_smtp_instance

        from emails.backend.smtp.aio_client import AsyncSMTPClientWithResponse
        client = AsyncSMTPClientWithResponse(parent=parent, host='localhost', port=25)

        response = await client.sendmail(
            from_addr='sender@example.com',
            to_addrs=[],
            msg=b'Subject: test\r\n\r\nHello',
        )
        assert response is None


@pytest.mark.asyncio
async def test_sendmail_recipient_refused(parent):
    with patch('emails.backend.smtp.aio_client.aiosmtplib') as mock_aio:
        mock_smtp_instance = AsyncMock()
        mock_aio.SMTP.return_value = mock_smtp_instance
        mock_smtp_instance.supports_extension = MagicMock(return_value=False)
        mock_smtp_instance.mail.return_value = _aio_resp(250, 'OK')

        # All recipients refused
        exc = MagicMock()
        exc.code = 550
        exc.message = 'User unknown'
        mock_aio.SMTPRecipientRefused = type('SMTPRecipientRefused', (Exception,), {})
        refuse_exc = mock_aio.SMTPRecipientRefused(550, 'User unknown', 'bad@example.com')
        refuse_exc.code = 550
        refuse_exc.message = 'User unknown'
        mock_smtp_instance.rcpt.side_effect = refuse_exc
        mock_aio.SMTPRecipientsRefused = type('SMTPRecipientsRefused', (Exception,), {})

        from emails.backend.smtp.aio_client import AsyncSMTPClientWithResponse
        client = AsyncSMTPClientWithResponse(parent=parent, host='localhost', port=25)

        response = await client.sendmail(
            from_addr='sender@example.com',
            to_addrs=['bad@example.com'],
            msg=b'Subject: test\r\n\r\nHello',
        )

        assert response is not None
        assert not response.success
        assert 'bad@example.com' in response.refused_recipients


@pytest.mark.asyncio
async def test_sendmail_sender_refused(parent):
    with patch('emails.backend.smtp.aio_client.aiosmtplib') as mock_aio:
        mock_smtp_instance = AsyncMock()
        mock_aio.SMTP.return_value = mock_smtp_instance
        mock_smtp_instance.supports_extension = MagicMock(return_value=False)

        # Sender refused via exception
        mock_aio.SMTPSenderRefused = type('SMTPSenderRefused', (Exception,), {})
        exc = mock_aio.SMTPSenderRefused(553, 'Sender rejected', 'bad@sender.com')
        exc.code = 553
        exc.message = 'Sender rejected'
        mock_smtp_instance.mail.side_effect = exc

        from emails.backend.smtp.aio_client import AsyncSMTPClientWithResponse
        client = AsyncSMTPClientWithResponse(parent=parent, host='localhost', port=25)

        response = await client.sendmail(
            from_addr='bad@sender.com',
            to_addrs=['rcpt@example.com'],
            msg=b'Subject: test\r\n\r\nHello',
        )

        assert response is not None
        assert not response.success
        assert response.error is not None


@pytest.mark.asyncio
async def test_ssl_and_tls_flags(parent):
    """Test that ssl=True sets use_tls=True and tls=True sets start_tls=True."""
    with patch('emails.backend.smtp.aio_client.aiosmtplib') as mock_aio:
        mock_smtp_instance = AsyncMock()
        mock_aio.SMTP.return_value = mock_smtp_instance

        from emails.backend.smtp.aio_client import AsyncSMTPClientWithResponse

        # ssl=True should pass use_tls=True
        client_ssl = AsyncSMTPClientWithResponse(parent=parent, host='localhost', port=465, ssl=True)
        call_kwargs = mock_aio.SMTP.call_args
        assert call_kwargs[1]['use_tls'] is True
        assert call_kwargs[1]['start_tls'] is False

        # tls=True should pass start_tls=True
        client_tls = AsyncSMTPClientWithResponse(parent=parent, host='localhost', port=587, tls=True)
        call_kwargs = mock_aio.SMTP.call_args
        assert call_kwargs[1]['start_tls'] is True
        assert call_kwargs[1]['use_tls'] is False


@pytest.mark.asyncio
async def test_quit_handles_disconnect(parent):
    """Test that quit() handles SMTPServerDisconnected gracefully."""
    with patch('emails.backend.smtp.aio_client.aiosmtplib') as mock_aio:
        mock_smtp_instance = AsyncMock()
        mock_aio.SMTP.return_value = mock_smtp_instance
        mock_aio.SMTPServerDisconnected = type('SMTPServerDisconnected', (Exception,), {})
        mock_smtp_instance.quit.side_effect = mock_aio.SMTPServerDisconnected()
        mock_smtp_instance.close = MagicMock()

        from emails.backend.smtp.aio_client import AsyncSMTPClientWithResponse
        client = AsyncSMTPClientWithResponse(parent=parent, host='localhost', port=25)

        # Should not raise
        await client.quit()
        mock_smtp_instance.close.assert_called_once()


@pytest.mark.asyncio
async def test_initialize_with_login(parent):
    """Test that initialize() performs connect and login when credentials provided."""
    with patch('emails.backend.smtp.aio_client.aiosmtplib') as mock_aio:
        mock_smtp_instance = AsyncMock()
        mock_aio.SMTP.return_value = mock_smtp_instance

        from emails.backend.smtp.aio_client import AsyncSMTPClientWithResponse
        client = AsyncSMTPClientWithResponse(
            parent=parent, host='localhost', port=587,
            tls=True, user='testuser', password='testpass',
        )
        await client.initialize()

        mock_smtp_instance.connect.assert_awaited_once()
        mock_smtp_instance.login.assert_awaited_once_with('testuser', 'testpass')


@pytest.mark.asyncio
async def test_sendmail_string_to_addrs(parent):
    """Test that sendmail handles a string to_addrs (not list)."""
    with patch('emails.backend.smtp.aio_client.aiosmtplib') as mock_aio:
        mock_smtp_instance = AsyncMock()
        mock_aio.SMTP.return_value = mock_smtp_instance
        mock_smtp_instance.supports_extension = MagicMock(return_value=False)
        mock_smtp_instance.mail.return_value = _aio_resp(250, 'OK')
        mock_smtp_instance.rcpt.return_value = _aio_resp(250, 'OK')
        mock_smtp_instance.data.return_value = _aio_resp(250, 'OK')

        from emails.backend.smtp.aio_client import AsyncSMTPClientWithResponse
        client = AsyncSMTPClientWithResponse(parent=parent, host='localhost', port=25)

        response = await client.sendmail(
            from_addr='sender@example.com',
            to_addrs='rcpt@example.com',  # string, not list
            msg=b'Subject: test\r\n\r\nHello',
        )

        assert response is not None
        assert response.success
        assert response.to_addrs == ['rcpt@example.com']
