Features
--------

-  HTML-email message abstraction
-  Method to transform html body:

   - css inlining (using peterbe's premailer)
   - image inlining
-  DKIM signature
-  Message loaders
-  Send directly or via django email backend


Examples
--------

Create message:

.. code-block:: python

    import emails
    message = emails.html(html=open('letter.html'),
                          subject='Friday party',
                          mail_from=('Company Team', 'contact@mycompany.com'))


Attach files or inline images:

.. code-block:: python

    message.attach(data=open('event.ics'), filename='Event.ics')
    message.attach(data=open('image.png'), filename='image.png',
                   content_disposition='inline')

Use templates:

.. code-block:: python

    from emails.template import JinjaTemplate as T

    message = emails.html(subject=T('Payment Receipt No.{{ billno }}'),
                          html=T('<p>Dear {{ name }}! This is a receipt...'),
                          mail_from=('ABC', 'robot@mycompany.com'))

    message.send(to=('John Brown', 'jbrown@gmail.com'),
                 render={'name': 'John Brown', 'billno': '141051906163'})



Add DKIM signature:

.. code-block:: python

    message.dkim(key=open('my.key'), domain='mycompany.com', selector='newsletter')

Generate email.message or rfc822 string:

.. code-block:: python

    m = message.as_message()
    s = message.as_string()


Send and get response from smtp server:

.. code-block:: python

    r = message.send(to=('John Brown', 'jbrown@gmail.com'),
                     render={'name': 'John'},
                     smtp={'host':'smtp.mycompany.com', 'port': 465, 'ssl': True})
    assert r.status_code == 250


Django
------

DjangoMessage helper sends via django configured email backend:

.. code-block:: python

    from emails.django import DjangoMessage as Message
    message = Message(...)
    message.send(mail_to=('John Brown', 'jbrown@gmail.com'),
                 context={'name': 'John'})

Flask
-----

For flask integration take a look at `flask-emails <https://github.com/lavr/flask-emails>`_
