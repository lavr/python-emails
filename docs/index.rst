python-emails
=============

.. module:: emails

|pypi| |python| |license|

.. |pypi| image:: https://img.shields.io/pypi/v/emails.svg
   :target: https://pypi.org/project/emails/
   :alt: PyPI version

.. |python| image:: https://img.shields.io/pypi/pyversions/emails.svg
   :target: https://pypi.org/project/emails/
   :alt: Python versions

.. |license| image:: https://img.shields.io/pypi/l/emails.svg
   :target: https://github.com/lavr/python-emails/blob/master/LICENSE
   :alt: License

Modern email handling in python. Build, transform, and send emails with a
clean, intuitive API.

.. code-block:: python

    import emails

    message = emails.html(
        subject="Hi from python-emails!",
        html="<html><p>Hello, <strong>World!</strong></p></html>",
        mail_from=("Alice", "alice@example.com"),
    )
    response = message.send(
        to="bob@example.com",
        smtp={"host": "smtp.example.com", "port": 587, "tls": True},
    )
    assert response.status_code == 250


.. rubric:: Features

- Build HTML and plain-text emails with a simple API
- CSS inlining, image embedding, and HTML cleanup via built-in transformations
- Jinja2, Mako, and string templates for dynamic content
- Inline images and file attachments
- DKIM signing
- Load messages from URLs, HTML files, directories, ZIP archives, or RFC 822 files
- Django integration via ``DjangoMessage``
- SMTP sending with SSL/TLS support
- Async sending via ``aiosmtplib``


.. toctree::
   :maxdepth: 2

   quickstart
   transformations
   advanced
   api
   faq
   install
   howtohelp
   links
