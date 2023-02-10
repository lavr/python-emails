python-emails
~~~~~~~~~~~~~

Modern python library for email.

Build message:

.. code-block:: python

   >>> import emails
   >>> message = emails.html(html="<p>Hi!<br>Here is your receipt...",
                          subject="Your receipt No. 567098123",
                          mail_from=('Some Store', 'store@somestore.com'))
   >>> message.attach(data=open('bill.pdf', 'rb'), filename='bill.pdf')

send message and get response from smtp server:

.. code-block:: python

   >>> r = message.send(to='s@lavr.me', smtp={'host': 'aspmx.l.google.com', 'timeout': 5})
   >>> assert r.status_code == 250


add CC in the Email

.. code-block:: python
   
   >>> r =  message.set_cc(['someone@gmail.com'])
 
add BCC in the Email 

.. code-block:: python

   >>> r = message.set_bcc(['someone@gmail.com', 'anyone@gmail.com'])


and more:

* DKIM signature
* Render body from template
* Flask extension and Django integration
* Message body transformation methods
* Load message from url or from file

|

Documentation: `python-emails.readthedocs.org <http://python-emails.readthedocs.org/>`_

Flask extension: `flask-emails <https://github.com/lavr/flask-emails>`_

|
|

.. image:: https://github.com/lavr/python-emails/workflows/Tests/badge.svg?branch=master
   :target: https://github.com/lavr/python-emails/actions?query=workflow%3ATests

.. image:: https://img.shields.io/pypi/v/emails.svg
   :target: https://pypi.python.org/pypi/emails

.. image:: https://coveralls.io/repos/lavr/python-emails/badge.svg?branch=master
   :target: https://coveralls.io/r/lavr/python-emails?branch=master
