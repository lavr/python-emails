FAQ
===

Frequently asked questions about ``python-emails``.


How do I send through Gmail / Yandex / other providers?
-------------------------------------------------------

All SMTP providers follow the same pattern — pass the provider's SMTP
host, port, and credentials in the ``smtp`` dict:

.. code-block:: python

    response = message.send(
        to="recipient@example.com",
        smtp={
            "host": "<provider SMTP host>",
            "port": 587,
            "tls": True,
            "user": "your-email@example.com",
            "password": "your-password-or-app-password"
        }
    )

Common SMTP settings:

.. list-table::
   :header-rows: 1
   :widths: 20 30 10 15

   * - Provider
     - Host
     - Port
     - Encryption
   * - Gmail
     - ``smtp.gmail.com``
     - 587
     - ``tls=True``
   * - Yandex
     - ``smtp.yandex.ru``
     - 465
     - ``ssl=True``
   * - Outlook / Hotmail
     - ``smtp-mail.outlook.com``
     - 587
     - ``tls=True``
   * - Yahoo Mail
     - ``smtp.mail.yahoo.com``
     - 465
     - ``ssl=True``

.. note::

   Most providers require an **app password** instead of your regular
   account password. Consult the provider's documentation:

   - `Gmail: Sign in with app passwords <https://support.google.com/accounts/answer/185833>`_
   - `Yandex: App passwords <https://yandex.com/support/id/authorization/app-passwords.html>`_
   - `Outlook: App passwords <https://support.microsoft.com/en-us/account-billing/using-app-passwords-with-apps-that-don-t-support-two-step-verification-5896ed9b-4263-e681-128a-a6f2979a7944>`_
   - `Yahoo: App passwords <https://help.yahoo.com/kb/generate-manage-third-party-passwords-sln15241.html>`_

   Provider settings and authentication requirements change over time.
   Always refer to the official documentation for up-to-date instructions.


How do I attach a PDF or Excel file?
-------------------------------------

Use :meth:`~emails.Message.attach` with the file's data and filename.
The MIME type is auto-detected from the filename extension:

.. code-block:: python

    # Attach a PDF
    message.attach(filename="report.pdf", data=open("report.pdf", "rb"))

    # Attach an Excel file
    message.attach(filename="data.xlsx", data=open("data.xlsx", "rb"))

    # Attach with an explicit MIME type
    message.attach(
        filename="archive.7z",
        data=open("archive.7z", "rb"),
        mime_type="application/x-7z-compressed"
    )

You can also attach in-memory data:

.. code-block:: python

    import io

    csv_data = "name,score\nAlice,95\nBob,87\n"
    message.attach(
        filename="scores.csv",
        data=io.BytesIO(csv_data.encode("utf-8"))
    )


How is python-emails different from smtplib + email.mime?
---------------------------------------------------------

``python-emails`` is built on top of the standard library's ``email`` and
``smtplib`` modules. The difference is the level of abstraction.

With ``python-emails``:

.. code-block:: python

    import emails
    from emails.template import JinjaTemplate as T

    message = emails.html(
        subject=T("Passed: {{ project_name }}#{{ build_id }}"),
        html=T("<html><p>Build passed: {{ project_name }} "
               "<img src='cid:icon.png'> ...</p></html>"),
        text=T("Build passed: {{ project_name }} ..."),
        mail_from=("CI", "ci@mycompany.com")
    )
    message.attach(filename="icon.png", data=open("icon.png", "rb"),
                   content_disposition="inline")

    message.send(
        to="somebody@mycompany.com",
        render={"project_name": "user/project1", "build_id": 121},
        smtp={"host": "smtp.mycompany.com", "port": 587, "tls": True,
              "user": "ci", "password": "secret"}
    )

The same message with the standard library alone:

.. container:: toggle

    .. code-block:: python

        import os
        import smtplib
        from email.utils import formataddr, formatdate, COMMASPACE
        from email.header import Header
        from email import encoders
        from email.mime.multipart import MIMEMultipart
        from email.mime.base import MIMEBase
        from email.mime.text import MIMEText
        from email.mime.image import MIMEImage
        import jinja2

        sender_name, sender_email = "CI", "ci@mycompany.com"
        recipient_addr = ["somebody@mycompany.com"]

        j = jinja2.Environment()
        ctx = {"project_name": "user/project1", "build_id": 121}
        html = j.from_string(
            "<html><p>Build passed: {{ project_name }} "
            "<img src='cid:icon.png'> ...</p></html>"
        ).render(**ctx)
        text = j.from_string("Build passed: {{ project_name }} ...").render(**ctx)
        subject = j.from_string(
            "Passed: {{ project_name }}#{{ build_id }}"
        ).render(**ctx)

        encoded_name = Header(sender_name, "utf-8").encode()
        msg_root = MIMEMultipart("mixed")
        msg_root["Date"] = formatdate(localtime=True)
        msg_root["From"] = formataddr((encoded_name, sender_email))
        msg_root["To"] = COMMASPACE.join(recipient_addr)
        msg_root["Subject"] = Header(subject, "utf-8")
        msg_root.preamble = "This is a multi-part message in MIME format."

        msg_related = MIMEMultipart("related")
        msg_root.attach(msg_related)
        msg_alternative = MIMEMultipart("alternative")
        msg_related.attach(msg_alternative)

        msg_text = MIMEText(text.encode("utf-8"), "plain", "utf-8")
        msg_alternative.attach(msg_text)
        msg_html = MIMEText(html.encode("utf-8"), "html", "utf-8")
        msg_alternative.attach(msg_html)

        with open("icon.png", "rb") as fp:
            msg_image = MIMEImage(fp.read())
            msg_image.add_header("Content-ID", "<icon.png>")
            msg_related.attach(msg_image)

        mail_server = smtplib.SMTP("smtp.mycompany.com", 587)
        mail_server.ehlo()
        try:
            mail_server.starttls()
            mail_server.ehlo()
        except smtplib.SMTPException as e:
            print(e)
        mail_server.login("ci", "secret")
        mail_server.send_message(msg_root)
        mail_server.quit()

The standard library version requires:

- Manual MIME tree construction (``MIMEMultipart`` nesting of ``mixed``,
  ``related``, and ``alternative`` parts)
- Explicit header encoding with ``Header``
- Manual ``Content-ID`` management for inline images
- Separate template rendering before message assembly
- Direct SMTP session management (``ehlo``, ``starttls``, ``login``,
  ``quit``)

``python-emails`` handles all of this internally.


How is python-emails different from django.core.mail?
-----------------------------------------------------

``django.core.mail`` is Django's built-in email module. It works well
within Django but has several limitations compared to ``python-emails``:

- **No HTML transformations** — ``django.core.mail`` sends HTML as-is.
  ``python-emails`` can inline CSS, embed images, and clean up unsafe
  tags via :meth:`~emails.Message.transform`.
- **No template integration** — with ``django.core.mail`` you render
  templates manually before passing HTML to the message.
  ``python-emails`` accepts template objects directly in ``html``,
  ``text``, and ``subject``.
- **No loaders** — ``python-emails`` can create messages from URLs, ZIP
  archives, directories, and ``.eml`` files.
- **No DKIM** — ``python-emails`` supports DKIM signing out of the box.
- **Django-only** — ``django.core.mail`` requires a Django project.
  ``python-emails`` works in any Python project.

If you are in a Django project and want to use ``python-emails``,
the :class:`~emails.django.DjangoMessage` class integrates with Django's
email backend:

.. code-block:: python

    from emails.django import DjangoMessage

    message = DjangoMessage(
        html="<p>Hello {{ name }}!</p>",
        subject="Welcome",
        mail_from="noreply@example.com"
    )
    message.send(to="user@example.com", context={"name": "Alice"})

See the :doc:`Django Integration <advanced>` section for more details.


How do I debug email sending?
-----------------------------

There are two levels of debugging: SMTP protocol tracing and Python
logging.


SMTP Protocol Trace
~~~~~~~~~~~~~~~~~~~

Set ``debug=1`` in the ``smtp`` dict to print the full SMTP conversation
to stdout:

.. code-block:: python

    response = message.send(
        to="user@example.com",
        smtp={"host": "smtp.example.com", "port": 587, "tls": True,
              "user": "me", "password": "secret", "debug": 1}
    )

This outputs every command and response exchanged with the SMTP server,
which is useful for diagnosing authentication failures, TLS issues, and
rejected recipients.


Python Logging
~~~~~~~~~~~~~~

The library uses Python's standard ``logging`` module. Enable it to see
connection events and retries:

.. code-block:: python

    import logging

    logging.basicConfig(level=logging.DEBUG)

    # Or enable only the emails loggers:
    logging.getLogger("emails.backend.smtp.backend").setLevel(logging.DEBUG)
    logging.getLogger("emails.backend.smtp.client").setLevel(logging.DEBUG)

Logger names used by the library:

- ``emails.backend.smtp.backend`` — connection management, retries
- ``emails.backend.smtp.client`` — SMTP client operations


Inspecting the Message
~~~~~~~~~~~~~~~~~~~~~~

Before sending, you can inspect the raw RFC 822 output:

.. code-block:: python

    print(message.as_string())

This shows the full MIME structure, headers, and encoded content —
useful for verifying that attachments, inline images, and headers are
correct.


Checking the Response
~~~~~~~~~~~~~~~~~~~~~

After sending, inspect the :class:`SMTPResponse` object:

.. code-block:: python

    response = message.send(to="user@example.com", smtp={...})

    print(f"Status: {response.status_code}")
    print(f"Text: {response.status_text}")
    print(f"Success: {response.success}")

    if response.error:
        print(f"Error: {response.error}")

    if response.refused_recipients:
        for addr, (code, reason) in response.refused_recipients.items():
            print(f"Refused {addr}: {code} {reason}")
