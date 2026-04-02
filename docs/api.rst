API Reference
=============

This section documents the public API of the ``python-emails`` library.


Message
-------

The :class:`Message` class is the main entry point for creating and sending emails.

.. class:: Message(\*\*kwargs)

   Create a new email message.

   :param html: HTML body content (string or file-like object).
   :type html: str or None
   :param text: Plain text body content (string or file-like object).
   :type text: str or None
   :param subject: Email subject line. Supports template rendering.
   :type subject: str or None
   :param mail_from: Sender address. Accepts a string ``"user@example.com"`` or
       a tuple ``("Display Name", "user@example.com")``.
   :type mail_from: str or tuple or None
   :param mail_to: Recipient address(es). Accepts a string, tuple, or list of strings/tuples.
   :type mail_to: str or tuple or list or None
   :param cc: CC recipient(s). Same format as ``mail_to``.
   :type cc: str or tuple or list or None
   :param bcc: BCC recipient(s). Same format as ``mail_to``.
   :type bcc: str or tuple or list or None
   :param reply_to: Reply-To address(es). Same format as ``mail_to``.
   :type reply_to: str or tuple or list or None
   :param headers: Custom email headers as a dictionary.
   :type headers: dict or None
   :param headers_encoding: Encoding for email headers (default: ``'ascii'``).
   :type headers_encoding: str or None
   :param attachments: List of attachments (dicts or :class:`BaseFile` objects).
   :type attachments: list or None
   :param charset: Message character set (default: ``'utf-8'``).
   :type charset: str or None
   :param message_id: Message-ID header value. Can be a string, a :class:`MessageID` instance,
       ``False`` to omit, or ``None`` to auto-generate.
   :type message_id: str or :class:`~emails.utils.MessageID` or bool or None
   :param date: Date header value. Accepts a string, :class:`~datetime.datetime`, float (timestamp),
       ``False`` to omit, or a callable that returns one of these types.
   :type date: str or datetime or float or bool or callable or None

   Example::

       import emails

       msg = emails.Message(
           html="<p>Hello, World!</p>",
           subject="Test Email",
           mail_from=("Sender", "sender@example.com"),
           mail_to="recipient@example.com"
       )


Message Methods
~~~~~~~~~~~~~~~

.. method:: Message.send(to=None, set_mail_to=True, mail_from=None, set_mail_from=False, render=None, smtp_mail_options=None, smtp_rcpt_options=None, smtp=None)

   Send the message via SMTP.

   :param to: Override recipient address(es).
   :param set_mail_to: If ``True``, update the message's ``mail_to`` with ``to``.
   :param mail_from: Override sender address.
   :param set_mail_from: If ``True``, update the message's ``mail_from``.
   :param render: Dictionary of template variables for rendering.
   :param smtp_mail_options: SMTP MAIL command options.
   :param smtp_rcpt_options: SMTP RCPT command options.
   :param smtp: SMTP configuration. Either a dict with connection parameters
       (``host``, ``port``, ``ssl``, ``tls``, ``user``, ``password``, ``timeout``)
       or an :class:`SMTPBackend` instance.
   :returns: :class:`SMTPResponse` or ``None``

   Example::

       response = msg.send(
           to="user@example.com",
           smtp={"host": "smtp.example.com", "port": 587, "tls": True,
                 "user": "login", "password": "secret"}
       )

.. method:: Message.send_async(to=None, set_mail_to=True, mail_from=None, set_mail_from=False, render=None, smtp_mail_options=None, smtp_rcpt_options=None, smtp=None)

   Send the message via SMTP asynchronously. Requires ``aiosmtplib``
   (install with ``pip install "emails[async]"``).

   Parameters are the same as :meth:`send`, except ``smtp`` accepts a dict
   or an :class:`AsyncSMTPBackend` instance.

   When ``smtp`` is a dict, a temporary :class:`AsyncSMTPBackend` is created
   and closed after sending. When an existing backend is passed, the caller
   is responsible for closing it.

   :returns: :class:`SMTPResponse` or ``None``

   Example::

       response = await msg.send_async(
           to="user@example.com",
           smtp={"host": "smtp.example.com", "port": 587, "tls": True,
                 "user": "login", "password": "secret"}
       )

   Using a shared backend for multiple sends::

       from emails.backend.smtp.aio_backend import AsyncSMTPBackend

       async with AsyncSMTPBackend(host="smtp.example.com", port=587,
                                   tls=True, user="login",
                                   password="secret") as backend:
           for msg in messages:
               await msg.send_async(smtp=backend)

.. method:: Message.attach(\*\*kwargs)

   Attach a file to the message. Sets ``content_disposition`` to ``'attachment'``
   by default.

   :param filename: Name of the attached file.
   :param data: File content as bytes or a file-like object.
   :param content_disposition: ``'attachment'`` (default) or ``'inline'``.
   :param mime_type: MIME type of the file. Auto-detected from filename if not specified.

   Example::

       msg.attach(filename="report.pdf", data=open("report.pdf", "rb"))
       msg.attach(filename="logo.png", data=img_data, content_disposition="inline")

.. method:: Message.render(\*\*kwargs)

   Set template rendering data. Template variables are substituted when
   accessing ``html_body``, ``text_body``, or ``subject``.

   :param kwargs: Key-value pairs used as template context.

   Example::

       msg = emails.Message(
           html=emails.template.JinjaTemplate("<p>Hello {{ name }}</p>"),
           subject=emails.template.JinjaTemplate("Welcome, {{ name }}")
       )
       msg.render(name="World")

.. method:: Message.as_string(message_cls=None)

   Return the message as a string, including DKIM signature if configured.

   :param message_cls: Optional custom MIME message class.
   :returns: Message as a string.
   :rtype: str

.. method:: Message.as_bytes(message_cls=None)

   Return the message as bytes, including DKIM signature if configured.

   :param message_cls: Optional custom MIME message class.
   :returns: Message as bytes.
   :rtype: bytes

.. method:: Message.as_message(message_cls=None)

   Return the underlying MIME message object.

   :param message_cls: Optional custom MIME message class.
   :returns: MIME message object.

.. method:: Message.transform(\*\*kwargs)

   Apply HTML transformations to the message body. Loads and processes the HTML
   content through the transformer.

   See the HTML Transformations section for available parameters.

.. method:: Message.dkim(key, domain, selector, ignore_sign_errors=False, \*\*kwargs)

   Configure DKIM signing for the message. The signature is applied when
   the message is serialized via :meth:`as_string`, :meth:`as_bytes`,
   or :meth:`send`.

   This method is also available as :meth:`sign`.

   :param key: Private key for signing (PEM format). String, bytes, or file-like object.
   :param domain: DKIM domain (e.g., ``"example.com"``).
   :param selector: DKIM selector (e.g., ``"default"``).
   :param ignore_sign_errors: If ``True``, suppress signing exceptions.
   :returns: The message instance (for chaining).
   :rtype: Message

   Example::

       msg.dkim(key=open("private.pem"), domain="example.com", selector="default")


Message Properties
~~~~~~~~~~~~~~~~~~

.. attribute:: Message.html

   Get or set the HTML body content.

.. attribute:: Message.text

   Get or set the plain text body content.

.. attribute:: Message.html_body

   The rendered HTML body (read-only). If templates are used, returns the
   rendered result; otherwise returns the raw HTML.

.. attribute:: Message.text_body

   The rendered text body (read-only). If templates are used, returns the
   rendered result; otherwise returns the raw text.

.. attribute:: Message.mail_from

   Get or set the sender address. Returns a ``(name, email)`` tuple.

.. attribute:: Message.mail_to

   Get or set the recipient address(es). Returns a list of ``(name, email)`` tuples.

.. attribute:: Message.cc

   Get or set CC recipient(s). Returns a list of ``(name, email)`` tuples.

.. attribute:: Message.bcc

   Get or set BCC recipient(s). Returns a list of ``(name, email)`` tuples.

.. attribute:: Message.reply_to

   Get or set Reply-To address(es). Returns a list of ``(name, email)`` tuples.

.. attribute:: Message.subject

   Get or set the email subject. Supports template rendering.

.. attribute:: Message.message_id

   Get or set the Message-ID header value.

.. attribute:: Message.date

   Get or set the Date header value.

.. attribute:: Message.charset

   Get or set the message character set (default: ``'utf-8'``).

.. attribute:: Message.headers_encoding

   Get or set the encoding for email headers (default: ``'ascii'``).

.. attribute:: Message.attachments

   Access the attachment store (:class:`MemoryFileStore`). Lazily initialized.

.. attribute:: Message.render_data

   Get or set the template rendering context dictionary.

.. attribute:: Message.transformer

   Access the HTML transformer for custom image/link transformations.
   Lazily created on first access. See the :doc:`HTML Transformations <transformations>`
   section for usage examples.


SMTPResponse
------------

Returned by :meth:`Message.send`. Contains information about the SMTP transaction.

.. class:: SMTPResponse

   .. attribute:: status_code

      The SMTP status code from the last command (e.g., ``250`` for success).
      ``None`` if the transaction was not completed.

   .. attribute:: status_text

      The SMTP status text from the last command, as bytes.

   .. attribute:: success

      ``True`` if the message was sent successfully (status code is ``250``
      and the transaction completed).

   .. attribute:: error

      The exception object if an error occurred, or ``None``.

   .. attribute:: refused_recipients

      A dictionary mapping refused recipient email addresses to
      ``(code, message)`` tuples.

   .. attribute:: last_command

      The last SMTP command that was sent (e.g., ``'mail'``, ``'rcpt'``, ``'data'``).

   Example::

       response = msg.send(smtp={"host": "localhost"})
       if response.success:
           print("Sent!")
       else:
           print(f"Failed: {response.status_code} {response.status_text}")
           if response.error:
               print(f"Error: {response.error}")
           if response.refused_recipients:
               print(f"Refused: {response.refused_recipients}")


AsyncSMTPBackend
----------------

For async sending via :meth:`Message.send_async`. Requires ``aiosmtplib``
(install with ``pip install "emails[async]"``).

.. class:: emails.backend.smtp.aio_backend.AsyncSMTPBackend(ssl=False, fail_silently=True, mail_options=None, \*\*kwargs)

   Manages an async SMTP connection. Supports ``async with`` for automatic cleanup.

   :param host: SMTP server hostname.
   :param port: SMTP server port.
   :param ssl: Use implicit TLS (SMTPS).
   :param tls: Use STARTTLS after connecting.
   :param user: SMTP username for authentication.
   :param password: SMTP password for authentication.
   :param timeout: Connection timeout in seconds (default: ``5``).
   :param fail_silently: If ``True`` (default), SMTP errors are captured in the
       response rather than raised.
   :param mail_options: Default SMTP MAIL command options.

   .. method:: sendmail(from_addr, to_addrs, msg, mail_options=None, rcpt_options=None)
      :async:

      Send a message. Automatically retries once on server disconnect.

      :returns: :class:`SMTPResponse` or ``None``

   .. method:: close()
      :async:

      Close the SMTP connection.

   Example::

       from emails.backend.smtp.aio_backend import AsyncSMTPBackend

       async with AsyncSMTPBackend(host="smtp.example.com", port=587,
                                   tls=True, user="me",
                                   password="secret") as backend:
           response = await backend.sendmail(
               from_addr="sender@example.com",
               to_addrs=["recipient@example.com"],
               msg=message
           )


Loaders
-------

Loader functions create :class:`Message` instances from various sources.

All loaders are available in the ``emails.loader`` module.

.. function:: emails.loader.from_html(html, text=None, base_url=None, message_params=None, local_loader=None, template_cls=None, message_cls=None, source_filename=None, requests_params=None, \*\*kwargs)

   Create a message from an HTML string. Images and stylesheets referenced
   in the HTML can be automatically loaded and embedded.

   :param html: HTML content as a string.
   :param text: Optional plain text alternative.
   :param base_url: Base URL for resolving relative URLs in the HTML.
   :param message_params: Additional parameters passed to the Message constructor.
   :param local_loader: A loader instance for resolving local file references.
   :param template_cls: Template class to use for the HTML body.
   :param message_cls: Custom Message class to instantiate.
   :param source_filename: Filename hint for the source HTML.
   :param requests_params: Parameters passed to HTTP requests when fetching resources.
   :param kwargs: Additional transformer options.
   :returns: A :class:`Message` instance.

   ``from_string`` is an alias for this function.

.. function:: emails.loader.from_url(url, requests_params=None, \*\*kwargs)

   Create a message by downloading an HTML page from a URL.
   Images and stylesheets are fetched and embedded.

   :param url: URL of the HTML page.
   :param requests_params: Parameters passed to HTTP requests.
   :param kwargs: Additional transformer options.
   :returns: A :class:`Message` instance.

   ``load_url`` is an alias for this function.

.. function:: emails.loader.from_directory(directory, loader_cls=None, \*\*kwargs)

   Create a message from a local directory. The directory should contain
   an HTML file and any referenced images or attachments.

   :param directory: Path to the directory.
   :param loader_cls: Custom loader class.
   :param kwargs: Additional options (``html_filename``, ``text_filename``, ``message_params``).
   :returns: A :class:`Message` instance.

.. function:: emails.loader.from_zip(zip_file, loader_cls=None, \*\*kwargs)

   Create a message from a ZIP archive containing HTML and resources.

   :param zip_file: Path to ZIP file or a file-like object.
   :param loader_cls: Custom loader class.
   :param kwargs: Additional options (``html_filename``, ``text_filename``, ``message_params``).
   :returns: A :class:`Message` instance.

.. function:: emails.loader.from_file(filename, \*\*kwargs)

   Create a message from a single HTML file.

   :param filename: Path to the HTML file.
   :param kwargs: Additional options (``message_params``).
   :returns: A :class:`Message` instance.

.. function:: emails.loader.from_rfc822(msg, loader_cls=None, message_params=None, parse_headers=False)

   Create a message from an RFC 822 email object (e.g., from :mod:`email.message`).
   Primarily intended for demonstration and testing purposes.

   :param msg: An :class:`email.message.Message` object.
   :param loader_cls: Custom loader class.
   :param message_params: Additional parameters for the Message constructor.
   :param parse_headers: If ``True``, parse and transfer email headers.
   :returns: A :class:`Message` instance.


Loader Exceptions
~~~~~~~~~~~~~~~~~

.. exception:: emails.loader.LoadError

   Base exception for all loader errors.

.. exception:: emails.loader.IndexFileNotFound

   Raised when the loader cannot find an HTML index file in the source.
   Subclass of :exc:`LoadError`.

.. exception:: emails.loader.InvalidHtmlFile

   Raised when the HTML content cannot be parsed.
   Subclass of :exc:`LoadError`.


Templates
---------

Template classes allow dynamic content in email bodies and subjects. Pass a
template instance as the ``html``, ``text``, or ``subject`` parameter of
:class:`Message`.

Install template dependencies with extras::

    pip install "emails[jinja]"   # for JinjaTemplate

.. class:: emails.template.JinjaTemplate(template_text, environment=None)

   Template using `Jinja2 <https://jinja.palletsprojects.com/>`_ syntax.

   :param template_text: Jinja2 template string.
   :param environment: Optional :class:`jinja2.Environment` instance.

   Example::

       from emails.template import JinjaTemplate

       msg = emails.Message(
           html=JinjaTemplate("<p>Hello {{ name }}!</p>"),
           subject=JinjaTemplate("Welcome, {{ name }}"),
           mail_from="noreply@example.com"
       )
       msg.send(render={"name": "Alice"}, smtp={"host": "localhost"})

.. class:: emails.template.StringTemplate(template_text, safe_substitute=True)

   Template using Python's :class:`string.Template` syntax (``$variable`` or
   ``${variable}``).

   :param template_text: Template string.
   :param safe_substitute: If ``True`` (default), undefined variables are left
       as-is. If ``False``, undefined variables raise :exc:`KeyError`.

   Example::

       from emails.template import StringTemplate

       msg = emails.Message(
           html=StringTemplate("<p>Hello $name!</p>"),
           mail_from="noreply@example.com"
       )

.. class:: emails.template.MakoTemplate(template_text, \*\*kwargs)

   Template using `Mako <https://www.makotemplates.org/>`_ syntax.
   Requires the ``mako`` package.

   :param template_text: Mako template string.
   :param kwargs: Additional parameters passed to :class:`mako.template.Template`.


DjangoMessage
-------------

A :class:`Message` subclass for use with Django's email backend.

.. class:: emails.django.DjangoMessage(\*\*kwargs)

   Accepts the same parameters as :class:`Message`. Integrates with
   Django's email sending infrastructure.

   .. method:: send(mail_to=None, set_mail_to=True, mail_from=None, set_mail_from=False, context=None, connection=None, to=None)

      Send the message through Django's email backend.

      :param context: Dictionary of template rendering variables
          (equivalent to ``render`` in :meth:`Message.send`).
      :param connection: A Django email backend connection instance
          (e.g., from ``django.core.mail.get_connection()``).
          If ``None``, uses the default backend.
      :param to: Alias for ``mail_to``.
      :returns: ``1`` if the message was sent successfully, ``0`` otherwise.
      :rtype: int

   Example::

       from emails.django import DjangoMessage

       msg = DjangoMessage(
           html="<p>Hello {{ name }}</p>",
           subject="Welcome",
           mail_from="noreply@example.com"
       )
       msg.send(to="user@example.com", context={"name": "Alice"})


DKIM
----

DKIM (DomainKeys Identified Mail) signing is configured via the
:meth:`Message.dkim` method (or its alias :meth:`Message.sign`).

Parameters:

- ``key`` -- Private key in PEM format. Accepts a string, bytes, or file-like object.
- ``domain`` -- The signing domain (e.g., ``"example.com"``).
- ``selector`` -- The DKIM selector (e.g., ``"default"``).
- ``ignore_sign_errors`` -- If ``True``, silently ignore signing errors
  instead of raising exceptions.
- Additional keyword arguments are passed to the DKIM library
  (e.g., ``canonicalize``, ``signature_algorithm``).

Returns the message instance (for chaining).

Example::

    import emails

    msg = emails.Message(
        html="<p>Signed message</p>",
        mail_from=("Sender", "sender@example.com"),
        subject="DKIM Test"
    )
    msg.dkim(
        key=open("private.pem").read(),
        domain="example.com",
        selector="default"
    )
    msg.send(to="recipient@example.com", smtp={"host": "localhost"})

The signature is automatically applied when the message is serialized
(via :meth:`~Message.as_string`, :meth:`~Message.as_bytes`, or :meth:`~Message.send`).


Exceptions
----------

.. exception:: emails.HTTPLoaderError

   Raised when loading content from a URL fails (e.g., HTTP error, connection timeout).

.. exception:: emails.BadHeaderError

   Raised when an email header contains invalid characters (such as newlines
   or carriage returns).

.. exception:: emails.IncompleteMessage

   Raised when attempting to send a message that lacks required content
   (no HTML and no text body).

See also the `Loader Exceptions`_ section for loader-specific exceptions:
``LoadError``, ``IndexFileNotFound``, ``InvalidHtmlFile``.


Utilities
---------

.. class:: emails.utils.MessageID(domain=None, idstring=None)

   Generator for RFC 2822 compliant Message-ID values.

   :param domain: Domain part of the Message-ID. Defaults to the machine's FQDN.
   :param idstring: Optional additional string to strengthen uniqueness.

   The instance is callable — each call generates a new unique Message-ID.

   Example::

       from emails.utils import MessageID

       # Auto-generate a new Message-ID for each send
       msg = emails.Message(
           message_id=MessageID(domain="example.com"),
           html="<p>Hello</p>",
           mail_from="sender@example.com"
       )

.. function:: emails.html(\*\*kwargs)

   Convenience function that creates and returns a :class:`Message` instance.
   Accepts all the same parameters as the :class:`Message` constructor.

   Example::

       msg = emails.html(
           html="<p>Hello!</p>",
           subject="Test",
           mail_from="sender@example.com"
       )
