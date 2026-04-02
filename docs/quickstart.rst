Quickstart
==========

``python-emails`` is a library for composing and sending email messages
in Python. It provides a clean, high-level API over the standard library's
``email`` and ``smtplib`` modules.

With ``smtplib`` and ``email.mime``, sending an HTML email with an attachment
requires assembling MIME parts manually, encoding headers, handling character
sets, and managing the SMTP connection — often 30+ lines of boilerplate for
a simple message. ``python-emails`` reduces that to a few lines:

.. code-block:: python

    import emails

    message = emails.html(
        html="<p>Hello, World!</p>",
        subject="My first email",
        mail_from=("Me", "me@example.com")
    )
    response = message.send(to="you@example.com",
                            smtp={"host": "smtp.example.com", "port": 587,
                                  "tls": True, "user": "me", "password": "secret"})

The library handles MIME structure, character encoding, inline images,
CSS inlining, DKIM signing, and template rendering — things that are tedious
to do correctly with the standard library.


Creating a Message
------------------

The simplest way to create a message is :func:`emails.html`:

.. code-block:: python

    import emails

    message = emails.html(
        html="<h1>Friday party!</h1><p>You are invited.</p>",
        subject="Friday party",
        mail_from=("Company Team", "contact@mycompany.com")
    )

:func:`emails.html` is a shortcut for :class:`~emails.Message` — both accept
the same parameters:

- ``html`` — HTML body content (string or file-like object)
- ``text`` — plain text alternative
- ``subject`` — email subject line
- ``mail_from`` — sender address, as a string ``"user@example.com"`` or
  a tuple ``("Display Name", "user@example.com")``
- ``mail_to`` — recipient(s), same format as ``mail_from``; also accepts a list

You can also set ``cc``, ``bcc``, ``reply_to``, ``headers``, ``charset``,
and other parameters. See the :doc:`API Reference <api>` for full details.

If you have HTML in a file:

.. code-block:: python

    message = emails.html(
        html=open("letter.html"),
        subject="Newsletter",
        mail_from="newsletter@example.com"
    )


Sending a Message
-----------------

Call :meth:`~emails.Message.send` with an ``smtp`` dict describing
your SMTP server:

.. code-block:: python

    response = message.send(
        to="recipient@example.com",
        smtp={
            "host": "smtp.example.com",
            "port": 587,
            "tls": True,
            "user": "me@example.com",
            "password": "secret"
        }
    )

The ``smtp`` dict supports these keys:

- ``host`` — SMTP server hostname (default: ``"localhost"``)
- ``port`` — server port (default: ``25``)
- ``ssl`` — use SSL/TLS connection (for port 465)
- ``tls`` — use STARTTLS (for port 587)
- ``user`` — username for authentication
- ``password`` — password for authentication
- ``timeout`` — connection timeout in seconds (default: ``5``)

:meth:`~emails.Message.send` returns an :class:`SMTPResponse` object.
Check ``status_code`` to verify the message was accepted:

.. code-block:: python

    if response.status_code == 250:
        print("Message sent successfully")
    else:
        print(f"Send failed: {response.status_code}")


Attachments
-----------

Use :meth:`~emails.Message.attach` to add files to a message:

.. code-block:: python

    message.attach(filename="report.pdf", data=open("report.pdf", "rb"))
    message.attach(filename="data.csv", data=open("data.csv", "rb"))

Each attachment gets ``content_disposition='attachment'`` by default,
which means the file appears as a downloadable attachment in the recipient's
email client.

You can specify a MIME type explicitly:

.. code-block:: python

    message.attach(
        filename="event.ics",
        data=open("event.ics", "rb"),
        mime_type="text/calendar"
    )

If ``mime_type`` is not specified, it is auto-detected from the filename.


Inline Images
-------------

Inline images are embedded directly in the HTML body rather than shown as
attachments. They use the ``cid:`` (Content-ID) URI scheme to reference
embedded content.

To use an inline image:

1. Reference it in your HTML with ``cid:filename``
2. Attach it with ``content_disposition="inline"``

.. code-block:: python

    message = emails.html(
        html='<p>Hello! <img src="cid:logo.png"></p>',
        subject="With inline image",
        mail_from="sender@example.com"
    )
    message.attach(
        filename="logo.png",
        data=open("logo.png", "rb"),
        content_disposition="inline"
    )

The ``cid:logo.png`` in the HTML ``src`` attribute tells the email client
to display the attached file named ``logo.png`` inline at that position,
rather than as a separate attachment.


Templates
---------

For emails with dynamic content, use template classes instead of plain strings.
The most common choice is :class:`~emails.template.JinjaTemplate`, which uses
`Jinja2 <https://jinja.palletsprojects.com/>`_ syntax:

.. code-block:: python

    from emails.template import JinjaTemplate as T

    message = emails.html(
        subject=T("Payment Receipt No.{{ bill_no }}"),
        html=T("<p>Dear {{ name }},</p><p>Your payment of ${{ amount }} was received.</p>"),
        mail_from=("Billing", "billing@mycompany.com")
    )

Pass template variables via the ``render`` parameter of :meth:`~emails.Message.send`:

.. code-block:: python

    message.send(
        to="customer@example.com",
        render={"name": "Alice", "bill_no": "12345", "amount": "99.00"},
        smtp={"host": "smtp.example.com", "port": 587, "tls": True,
              "user": "billing", "password": "secret"}
    )

Templates work in ``html``, ``text``, and ``subject`` — all three are rendered
with the same variables.

Jinja2 templates require the ``jinja2`` package. Install it with::

    pip install "emails[jinja]"

Two other template backends are available:

- :class:`~emails.template.StringTemplate` — uses Python's
  :class:`string.Template` syntax (``$variable``)
- :class:`~emails.template.MakoTemplate` — uses
  `Mako <https://www.makotemplates.org/>`_ syntax (requires the ``mako`` package)


DKIM Signing
------------

DKIM (DomainKeys Identified Mail) lets the recipient verify that an email
was authorized by the domain owner. This improves deliverability and reduces
the chance of messages being marked as spam.

To sign a message, call :meth:`~emails.Message.dkim` with your private key,
domain, and selector:

.. code-block:: python

    message.dkim(
        key=open("private.pem", "rb"),
        domain="mycompany.com",
        selector="default"
    )

The signature is applied automatically when the message is sent or serialized.
The method returns the message instance, so you can chain it:

.. code-block:: python

    message = emails.html(
        html="<p>Signed message</p>",
        mail_from="sender@mycompany.com",
        subject="DKIM Test"
    ).dkim(key=open("private.pem", "rb"), domain="mycompany.com", selector="default")

DKIM requires a private key in PEM format and a corresponding DNS TXT record
on your domain. Consult your DNS provider's documentation for setting up
the DNS record.


Generating Without Sending
---------------------------

Sometimes you need the raw email content without actually sending it —
for example, to store it, pass it to another system, or inspect it.

:meth:`~emails.Message.as_string` returns the full RFC 822 message as a string:

.. code-block:: python

    raw = message.as_string()
    print(raw)

:meth:`~emails.Message.as_message` returns a standard library
:class:`email.message.Message` object, which you can inspect or manipulate:

.. code-block:: python

    msg = message.as_message()
    print(msg["Subject"])
    print(msg["From"])

There is also :meth:`~emails.Message.as_bytes` if you need the message
as bytes.

If DKIM signing is configured, the signature is included in the output
of all three methods.


Error Handling
--------------

:meth:`~emails.Message.send` returns an :class:`SMTPResponse` object.
It never raises an exception for SMTP errors by default — instead, error
information is available on the response:

.. code-block:: python

    response = message.send(
        to="recipient@example.com",
        smtp={"host": "smtp.example.com", "port": 587, "tls": True,
              "user": "me", "password": "secret"}
    )

    if response.success:
        print("Sent!")
    else:
        print(f"Failed with status {response.status_code}: {response.status_text}")

        # Check for connection/auth errors
        if response.error:
            print(f"Error: {response.error}")

        # Check for rejected recipients
        if response.refused_recipients:
            for addr, (code, reason) in response.refused_recipients.items():
                print(f"  Refused {addr}: {code} {reason}")

Key attributes of :class:`SMTPResponse`:

- ``success`` — ``True`` if the message was accepted (status code 250)
- ``status_code`` — the SMTP response code (``250``, ``550``, etc.), or ``None`` on connection failure
- ``status_text`` — the SMTP server's response text
- ``error`` — the exception object if a connection or protocol error occurred
- ``refused_recipients`` — a dict of recipients rejected by the server
- ``last_command`` — the last SMTP command that was attempted (``'mail'``, ``'rcpt'``, ``'data'``)
