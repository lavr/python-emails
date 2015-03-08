python-emails
~~~~~~~~~~~~~

Modern python library for email.

Build message:

.. code-block:: python

   >>> import emails
   >>> message = emails.html(html="<p>Hi!<br>Here is your receipt...",
                          subject="Your receipt No. 567098123",
                          mail_from=('Some Store', 'store@somestore.com'))
   >>> message.attach(data=open('bill.pdf'), filename='bill.pdf')

send message and get response from smtp server:

.. code-block:: python

   >>> r = message.send(to='s@lavr.me', smtp={'host': 'aspmx.l.google.com', 'timeout': 5})
   >>> assert r.status_code == 250

and more:

* DKIM signature
* Render body from template
* Flask extension and Django integration
* Message body transformation methods
* Load message from url or from file

|

See **documentation** on `python-emails.readthedocs.org <http://python-emails.readthedocs.org/>`_

|
|

.. image:: https://travis-ci.org/lavr/python-emails.png?branch=master
   :target: https://travis-ci.org/lavr/python-emails

.. image:: https://img.shields.io/pypi/v/emails.svg
   :target: https://pypi.python.org/pypi/emails

.. image:: http://allmychanges.com/p/python/emails/badge/
   :target: http://allmychanges.com/p/python/emails/?utm_source=badge

.. image:: https://coveralls.io/repos/lavr/python-emails/badge.svg?branch=master
   :target: https://coveralls.io/r/lavr/python-emails?branch=master
