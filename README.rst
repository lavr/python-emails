python-emails
=============

.. |pypi| image:: https://img.shields.io/pypi/v/emails.svg
   :target: https://pypi.org/project/emails/
   :alt: PyPI version

.. |python| image:: https://img.shields.io/pypi/pyversions/emails.svg
   :target: https://pypi.org/project/emails/
   :alt: Python versions

.. |tests| image:: https://github.com/lavr/python-emails/workflows/Tests/badge.svg?branch=master
   :target: https://github.com/lavr/python-emails/actions?query=workflow%3ATests
   :alt: Test status

.. |docs| image:: https://readthedocs.org/projects/python-emails/badge/?version=latest
   :target: https://python-emails.readthedocs.io/
   :alt: Documentation status

.. |license| image:: https://img.shields.io/pypi/l/emails.svg
   :target: https://github.com/lavr/python-emails/blob/master/LICENSE
   :alt: License

|pypi| |python| |tests| |docs| |license|

Build, transform, and send emails in Python with a high-level API.

``python-emails`` helps you compose HTML and plain-text messages, attach files,
embed inline images, render templates, apply HTML transformations, sign with
DKIM, and send through SMTP without hand-building MIME trees.


Why python-emails
-----------------

- A concise API over ``email`` and ``smtplib``
- HTML and plain-text messages in one object
- File attachments and inline images
- CSS inlining, image embedding, and HTML cleanup
- Jinja2, Mako, and string template support
- DKIM signing
- Loaders for URLs, HTML files, directories, ZIP archives, and RFC 822 messages
- SMTP sending with SSL/TLS support
- Async sending via ``aiosmtplib``


Quick Example
-------------

.. code-block:: python

    import emails

    message = emails.html(
        subject="Your receipt",
        html="<p>Hello!</p><p>Your payment was received.</p>",
        mail_from=("Billing", "billing@example.com"),
    )
    message.attach(filename="receipt.pdf", data=open("receipt.pdf", "rb"))

    response = message.send(
        to="customer@example.com",
        smtp={
            "host": "smtp.example.com",
            "port": 587,
            "tls": True,
            "user": "billing@example.com",
            "password": "app-password",
        },
    )
    assert response.status_code == 250


Installation
------------

Install the lightweight core:

.. code-block:: bash

    pip install emails

Install HTML transformation features such as CSS inlining, image embedding,
and loading from URLs or files:

.. code-block:: bash

    pip install "emails[html]"

Install Jinja2 template support for the ``JinjaTemplate`` class:

.. code-block:: bash

    pip install "emails[jinja]"

Install async SMTP sending support for ``send_async()``:

.. code-block:: bash

    pip install "emails[async]"


Common Tasks
------------

- Build and send your first message:
  `Quickstart <https://python-emails.readthedocs.io/en/latest/quickstart.html>`_
- Configure installation extras:
  `Install guide <https://python-emails.readthedocs.io/en/latest/install.html>`_
- Inline CSS, embed images, and customize HTML processing:
  `Advanced Usage <https://python-emails.readthedocs.io/en/latest/advanced.html>`_
- Learn the full public API:
  `API Reference <https://python-emails.readthedocs.io/en/latest/api.html>`_
- Troubleshoot common scenarios:
  `FAQ <https://python-emails.readthedocs.io/en/latest/faq.html>`_
- Explore alternatives and related projects:
  `Links <https://python-emails.readthedocs.io/en/latest/links.html>`_


What You Get
------------

- Message composition for HTML, plain text, headers, CC/BCC, and Reply-To
- Attachments, inline images, and MIME generation
- Template rendering in ``html``, ``text``, and ``subject``
- HTML transformations through ``message.transform()``
- SMTP delivery through config dicts or reusable backend objects
- Django integration via ``DjangoMessage``
- Flask integration via `flask-emails <https://github.com/lavr/flask-emails>`_


When To Use It
--------------

Use ``python-emails`` when you need more than a minimal plain-text SMTP call:
HTML emails, attachments, inline images, template rendering, DKIM, message
loading from external sources, or a cleaner API than hand-written
``email.mime`` code.

If you only need to send a very small plain-text message and want zero
dependencies, the standard library may be enough.


Documentation
-------------

- `Documentation home <https://python-emails.readthedocs.io/>`_
- `Quickstart <https://python-emails.readthedocs.io/en/latest/quickstart.html>`_
- `Advanced Usage <https://python-emails.readthedocs.io/en/latest/advanced.html>`_
- `API Reference <https://python-emails.readthedocs.io/en/latest/api.html>`_
- `FAQ <https://python-emails.readthedocs.io/en/latest/faq.html>`_


Project Status
--------------

``python-emails`` is production/stable software and currently supports
Python 3.10 through 3.14.


Contributing
------------

Issues and pull requests are welcome.

- `Report a bug or request a feature <https://github.com/lavr/python-emails/issues>`_
- `Source code on GitHub <https://github.com/lavr/python-emails>`_
- `How to Help <https://python-emails.readthedocs.io/en/latest/howtohelp.html>`_


License
-------

Apache 2.0. See `LICENSE <https://github.com/lavr/python-emails/blob/master/LICENSE>`_.
