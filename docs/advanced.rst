Advanced Usage
==============

This section covers advanced features and usage patterns of ``python-emails``.


SMTP Connections
----------------

By default, :meth:`~emails.Message.send` accepts an ``smtp`` dict and
manages the connection internally:

.. code-block:: python

    response = message.send(
        to="user@example.com",
        smtp={"host": "smtp.example.com", "port": 587, "tls": True,
              "user": "me", "password": "secret"}
    )

For more control, you can use :class:`~emails.backend.smtp.SMTPBackend`
directly.


Reusing Connections
~~~~~~~~~~~~~~~~~~~

When you call :meth:`~emails.Message.send` with the same ``smtp`` dict
on the same message, the library automatically reuses the SMTP connection
through an internal pool. Connections with identical parameters share
a backend:

.. code-block:: python

    smtp_config = {"host": "smtp.example.com", "port": 587, "tls": True,
                   "user": "me", "password": "secret"}

    # These two calls reuse the same underlying SMTP connection
    message.send(to="alice@example.com", smtp=smtp_config)
    message.send(to="bob@example.com", smtp=smtp_config)

For explicit connection management, create an :class:`SMTPBackend` instance
and pass it instead of a dict. The backend supports context managers:

.. code-block:: python

    from emails.backend.smtp import SMTPBackend

    with SMTPBackend(host="smtp.example.com", port=587,
                     tls=True, user="me", password="secret") as backend:
        for recipient in recipients:
            message.send(to=recipient, smtp=backend)
    # Connection is closed automatically


SSL vs STARTTLS
~~~~~~~~~~~~~~~

The library supports two encryption modes:

- **Implicit SSL** (``ssl=True``): Connects over TLS from the start.
  Typically used with port 465.

  .. code-block:: python

      message.send(smtp={"host": "mail.example.com", "port": 465, "ssl": True,
                         "user": "me", "password": "secret"})

- **STARTTLS** (``tls=True``): Connects in plain text, then upgrades to TLS.
  Typically used with port 587.

  .. code-block:: python

      message.send(smtp={"host": "smtp.example.com", "port": 587, "tls": True,
                         "user": "me", "password": "secret"})

You cannot set both ``ssl`` and ``tls`` to ``True`` -- this raises a
``ValueError``.


Timeouts
~~~~~~~~

The default socket timeout is 5 seconds. You can change it with the
``timeout`` parameter:

.. code-block:: python

    message.send(smtp={"host": "smtp.example.com", "timeout": 30})


Debugging
~~~~~~~~~

Enable SMTP protocol debugging to see the full conversation with the
server on stdout:

.. code-block:: python

    message.send(smtp={"host": "smtp.example.com", "debug": 1})


All SMTP Parameters
~~~~~~~~~~~~~~~~~~~

The full list of parameters accepted in the ``smtp`` dict (or as
:class:`SMTPBackend` constructor arguments):

- ``host`` -- SMTP server hostname
- ``port`` -- server port (int)
- ``ssl`` -- use implicit SSL/TLS (for port 465)
- ``tls`` -- use STARTTLS (for port 587)
- ``user`` -- authentication username
- ``password`` -- authentication password
- ``timeout`` -- socket timeout in seconds (default: ``5``)
- ``debug`` -- debug level (``0`` = off, ``1`` = verbose)
- ``fail_silently`` -- if ``True`` (default), return errors in the response
  instead of raising exceptions
- ``local_hostname`` -- FQDN for the EHLO/HELO command (auto-detected
  if not set)
- ``keyfile`` -- path to SSL key file
- ``certfile`` -- path to SSL certificate file
- ``mail_options`` -- list of ESMTP MAIL command options
  (e.g., ``["smtputf8"]``)


HTML Transformations
--------------------

The :meth:`~emails.Message.transform` method processes the HTML body
before sending -- inlining CSS, loading images, removing unsafe tags,
and more.

.. code-block:: python

    message = emails.Message(
        html="<style>h1{color:red}</style><h1>Hello!</h1>"
    )
    message.transform()

After transformation, the inline style is applied directly:

.. code-block:: python

    print(message.html)
    # <html><head></head><body><h1 style="color:red">Hello!</h1></body></html>


Parameters
~~~~~~~~~~

:meth:`~emails.Message.transform` accepts the following keyword arguments:

``css_inline`` (default: ``True``)
    Inline CSS styles using `premailer <https://github.com/peterbe/premailer>`_.
    External stylesheets referenced in ``<link>`` tags are loaded and
    converted to inline ``style`` attributes.

``remove_unsafe_tags`` (default: ``True``)
    Remove potentially dangerous HTML tags: ``<script>``, ``<object>``,
    ``<iframe>``, ``<frame>``, ``<base>``, ``<meta>``, ``<link>``,
    ``<style>``.

``set_content_type_meta`` (default: ``True``)
    Add a ``<meta http-equiv="Content-Type">`` tag to the ``<head>``
    with the message's charset.

``load_images`` (default: ``True``)
    Load images referenced in the HTML and embed them as message
    attachments. Accepts ``True``, ``False``, or a callable for custom
    filtering (see below).

``images_inline`` (default: ``False``)
    When ``True``, loaded images are embedded as inline attachments
    using ``cid:`` references instead of regular attachments.

The following parameters are **deprecated** and have no effect:

``make_links_absolute``
    Premailer always makes links absolute. Passing ``False`` triggers
    a ``DeprecationWarning``.

``update_stylesheet``
    Premailer does not support this feature. Passing ``True`` triggers
    a ``DeprecationWarning``.


Custom Image Filtering
~~~~~~~~~~~~~~~~~~~~~~

Pass a callable as ``load_images`` to control which images are loaded:

.. code-block:: python

    def should_load(element, hints=None, **kwargs):
        # Skip tracking pixels
        src = element.attrib.get("src", "")
        if "track" in src or "pixel" in src:
            return False
        return True

    message.transform(load_images=should_load)

You can also use the ``data-emails`` attribute in your HTML to control
individual images:

- ``data-emails="ignore"`` -- skip loading this image
- ``data-emails="inline"`` -- load as an inline attachment


Custom Link and Image Transformations
--------------------------------------

For more specific transformations, access the ``transformer`` property
directly.


Transforming Image URLs
~~~~~~~~~~~~~~~~~~~~~~~

:meth:`~emails.transformer.HTMLParser.apply_to_images` applies a function
to all image references in the HTML -- ``<img src>``, ``background``
attributes, and CSS ``url()`` values in ``style`` attributes:

.. code-block:: python

    message = emails.Message(html='<img src="promo.png">')
    message.transformer.apply_to_images(
        func=lambda src, **kw: "https://cdn.example.com/images/" + src
    )
    message.transformer.save()

    print(message.html)
    # <html><body><img src="https://cdn.example.com/images/promo.png"></body></html>

The callback receives ``uri`` (the current URL) and ``element`` (the lxml
element), and should return the new URL.

You can limit the scope with keyword arguments:

- ``images=True`` -- apply to ``<img src>`` (default: ``True``)
- ``backgrounds=True`` -- apply to ``background`` attributes (default: ``True``)
- ``styles_uri=True`` -- apply to CSS ``url()`` in style attributes (default: ``True``)


Transforming Link URLs
~~~~~~~~~~~~~~~~~~~~~~

:meth:`~emails.transformer.HTMLParser.apply_to_links` applies a function
to all ``<a href>`` values:

.. code-block:: python

    message = emails.Message(html='<a href="/about">About</a>')
    message.transformer.apply_to_links(
        func=lambda href, **kw: "https://example.com" + href
    )
    message.transformer.save()

    print(message.html)
    # <html><body><a href="https://example.com/about">About</a></body></html>

Always call ``message.transformer.save()`` after using ``apply_to_images``
or ``apply_to_links`` to update the message's HTML body.


Making Images Inline Manually
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

You can mark individual attachments as inline and synchronize the HTML
references:

.. code-block:: python

    message = emails.Message(html='<img src="promo.png">')
    message.attach(filename="promo.png", data=open("promo.png", "rb"))
    message.attachments["promo.png"].is_inline = True
    message.transformer.synchronize_inline_images()
    message.transformer.save()

    print(message.html)
    # <html><body><img src="cid:promo.png"></body></html>


Loaders
-------

Loader functions create :class:`Message` instances from various sources,
automatically handling HTML parsing, CSS inlining, and image embedding.
All loaders are in the ``emails.loader`` module.


Loading from a URL
~~~~~~~~~~~~~~~~~~

:func:`~emails.loader.from_url` fetches an HTML page and embeds all
referenced images and stylesheets:

.. code-block:: python

    import emails.loader

    message = emails.loader.from_url(
        url="https://example.com/newsletter/2024-01/index.html",
        requests_params={"timeout": 30}
    )

The ``requests_params`` dict is passed to the underlying HTTP requests
(for controlling timeouts, SSL verification, headers, etc.).


Loading from a ZIP Archive
~~~~~~~~~~~~~~~~~~~~~~~~~~

:func:`~emails.loader.from_zip` reads an HTML file and its resources
from a ZIP archive. The archive must contain at least one ``.html`` file:

.. code-block:: python

    message = emails.loader.from_zip(
        open("template.zip", "rb"),
        message_params={"subject": "Newsletter", "mail_from": "news@example.com"}
    )


Loading from a Directory
~~~~~~~~~~~~~~~~~~~~~~~~

:func:`~emails.loader.from_directory` loads from a local directory.
It looks for ``index.html`` (or ``index.htm``) automatically:

.. code-block:: python

    message = emails.loader.from_directory(
        "/path/to/email-template/",
        message_params={"subject": "Welcome", "mail_from": "hello@example.com"}
    )


Loading from a File
~~~~~~~~~~~~~~~~~~~

:func:`~emails.loader.from_file` loads from a single HTML file. Images
and CSS are resolved relative to the file's directory:

.. code-block:: python

    message = emails.loader.from_file("/path/to/email-template/welcome.html")


Loading from an .eml File
~~~~~~~~~~~~~~~~~~~~~~~~~

:func:`~emails.loader.from_rfc822` parses an RFC 822 email (e.g., a
``.eml`` file). Set ``parse_headers=True`` to copy Subject, From, To,
and other headers:

.. code-block:: python

    message = emails.loader.from_rfc822(
        open("archived.eml", "rb").read(),
        parse_headers=True
    )

This loader is primarily intended for demonstration and testing purposes.


When to Use Which Loader
~~~~~~~~~~~~~~~~~~~~~~~~~

- **from_html** -- you already have HTML as a string and want to
  process it (inline CSS, embed images)
- **from_url** -- the email template is hosted on a web server
- **from_directory** -- the template is a local folder with HTML, images,
  and CSS files
- **from_zip** -- the template is distributed as a ZIP archive
- **from_file** -- you have a single local HTML file
- **from_rfc822** -- you want to re-create a message from an existing
  ``.eml`` file


Django Integration
------------------

``python-emails`` provides :class:`~emails.django.DjangoMessage`, a
:class:`Message` subclass that sends through Django's email backend.

.. code-block:: python

    from emails.django import DjangoMessage

    message = DjangoMessage(
        html="<p>Hello {{ name }}!</p>",
        subject="Welcome",
        mail_from="noreply@example.com"
    )
    result = message.send(to="user@example.com", context={"name": "Alice"})

Key differences from :class:`Message`:

- Uses ``context`` instead of ``render`` for template variables.
- Uses Django's configured email backend (``django.core.mail.get_connection()``)
  instead of an ``smtp`` dict.
- Returns ``1`` on success and ``0`` on failure (matching Django's
  ``send_mail`` convention).
- Accepts an optional ``connection`` parameter for a custom Django email
  backend connection.

Using a custom Django connection:

.. code-block:: python

    from django.core.mail import get_connection
    from emails.django import DjangoMessage

    message = DjangoMessage(
        html="<p>Notification</p>",
        subject="Alert",
        mail_from="alerts@example.com"
    )

    connection = get_connection(backend="django.core.mail.backends.smtp.EmailBackend")
    message.send(to="admin@example.com", connection=connection)

Django email settings (``EMAIL_HOST``, ``EMAIL_PORT``, etc.) are used
automatically when no explicit connection is provided.


Flask Integration
-----------------

For Flask applications, use the
`flask-emails <https://github.com/lavr/flask-emails>`_ extension, which
provides Flask-specific integration (app factory support, configuration
from Flask config, etc.):

.. code-block:: python

    from flask_emails import Message

    message = Message(
        html="<p>Hello!</p>",
        subject="Test",
        mail_from="sender@example.com"
    )
    message.send(to="user@example.com")

Install with::

    pip install flask-emails

Refer to the `flask-emails documentation <https://github.com/lavr/flask-emails>`_
for configuration details.


Charset and Encoding
--------------------

``python-emails`` uses two separate encoding settings:

- ``charset`` -- encoding for the message body (default: ``'utf-8'``)
- ``headers_encoding`` -- encoding for email headers (default: ``'ascii'``)


Changing the Body Charset
~~~~~~~~~~~~~~~~~~~~~~~~~

For messages in specific encodings (e.g., Cyrillic), set the ``charset``
parameter:

.. code-block:: python

    message = emails.html(
        html="<p>Content in specific encoding</p>",
        charset="windows-1251",
        mail_from="sender@example.com"
    )

The library automatically registers proper encoding behaviors for common
charsets including ``utf-8``, ``windows-1251``, and ``koi8-r``.


Internationalized Domain Names (IDN)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Email addresses with internationalized domain names work with the
standard address format. The library handles encoding automatically:

.. code-block:: python

    message = emails.html(
        html="<p>Hello!</p>",
        mail_from=("Sender", "user@example.com"),
        mail_to=("Recipient", "user@example.com")
    )


Headers
-------

Custom Headers
~~~~~~~~~~~~~~

Pass a ``headers`` dict when creating a message to add custom email
headers:

.. code-block:: python

    message = emails.html(
        html="<p>Hello!</p>",
        subject="Test",
        mail_from="sender@example.com",
        headers={
            "X-Mailer": "python-emails",
            "X-Priority": "1",
            "List-Unsubscribe": "<mailto:unsubscribe@example.com>"
        }
    )

Non-ASCII characters in header values are automatically encoded
according to RFC 2047.

Header values are validated -- newline characters (``\n``, ``\r``)
raise :exc:`~emails.BadHeaderError` to prevent header injection attacks.


Reply-To, CC, and BCC
~~~~~~~~~~~~~~~~~~~~~~

These fields accept the same formats as ``mail_from`` and ``mail_to`` --
a string, a ``(name, email)`` tuple, or a list of either:

.. code-block:: python

    message = emails.html(
        html="<p>Hello!</p>",
        subject="Team update",
        mail_from=("Alice", "alice@example.com"),
        mail_to=[("Bob", "bob@example.com"), ("Carol", "carol@example.com")],
        cc="dave@example.com",
        bcc=["eve@example.com", "frank@example.com"],
        reply_to=("Alice", "alice-reply@example.com")
    )

- **CC** recipients are visible to all recipients in the email headers.
- **BCC** recipients receive the message but are not listed in the headers.
- **Reply-To** sets the address that email clients use when the recipient
  clicks "Reply".
