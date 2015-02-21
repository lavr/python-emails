python-emails
=============

Modern email handling in python.

Features
--------

-  HTML-email message abstraction
-  Method to transform html body:

   - css inlining (using peterbe's premailer)
   - image inlining
-  DKIM signature
-  Message loaders
-  Send directly or via django email backend


Examples:
---------

Create message:

::

    import emails
    message = emails.html(html=open('letter.html'),
                          subject='Friday party',
                          mail_from=('Company Team', 'contact@mycompany.com'))


Attach files or inline images:

::

    message.attach(data=open('event.ics'), filename='Event.ics')
    message.attach(data=open('image.png'), filename='image.png',
                   content_disposition='inline')

Use templates:

::

    from emails.template import JinjaTemplate as T

    message = emails.html(subject=T('Payment Receipt No.{{ billno }}'),
                          html=T('<p>Dear {{ name }}! This is a receipt...'),
                          mail_from=('ABC', 'robot@mycompany.com'))

    message.send(to=('John Brown', 'jbrown@gmail.com'),
                 render={'name': 'John Brown', 'billno': '141051906163'})



Add DKIM signature:

::

    message.dkim(key=open('my.key'), domain='mycompany.com', selector='newsletter')

Generate email.message or rfc822 string:

::

    m = message.as_message()
    s = message.as_string()



Send and get response from smtp server:

::

    r = message.send(to=('John Brown', 'jbrown@gmail.com'),
                     smtp={'host':'smtp.mycompany.com', 'port': 465, 'ssl': True})
    assert r.status_code == 250

Or send via Django email backend:

::
    from django.core.mail import get_connection
    from emails.message import DjangoMessageProxy
    c = django.core.mail.get_connection()
    c.send_messages([DjangoMessageProxy(message), ])


HTML transformer
----------------


Message HTML body can be modified with 'transformer' object:

::

    >>> message = emails.Message(html="<img src='promo.png'>")
    >>> message.transformer.apply_to_images(func=lambda src, **kw: 'http://mycompany.tld/images/'+src)
    >>> message.transformer.save()
    >>> message.html
    u'<html><body><img src="http://mycompany.tld/images/promo.png"></body></html>'

Code example to make images inline:

::

    >>> message = emails.Message(html="<img src='promo.png'>")
    >>> message.attach(filename='promo.png', data=open('promo.png'))
    >>> message.attachments['promo.png'].is_inline = True
    >>> message.transformer.synchronize_inline_images()
    >>> message.transformer.save()
    >>> message.html
    u'<html><body><img src="cid:promo.png"></body></html>'


Loaders
-------

python-emails ships with couple of loaders.

Load message from url:

::

    import emails.loader
    message = emails.loader.from_url(url="http://xxx.github.io/newsletter/2015-08-14/index.html")


Load from zipfile or directory:

::

    message = emails.loader.from_zipfile(open('design_pack.zip'))
    message = emails.loader.from_directory('/home/user/design_pack')

Zipfile and directory loaders require at least one html file (with "html" extension).


Install
-------

Install from pypi:

::

    $ [sudo] pip install emails

Install on Ubuntu from PPA:

::

    $ [sudo] add-apt-repository ppa:lavrme/python-emails-ppa
    $ [sudo] apt-get update
    $ [sudo] apt-get install python-emails



TODO
----

- Documentation
- 100% test coverage
- More accurate smtp session handling
- ESP integration: Amazon SES, SendGrid, ...
- deb package (ubuntu package almost done)
- rpm package
- Patch pydkim for performance (i.e. preload key once, not each time)
- Flask extension

How to Help
-----------

Library is under development and contributions are welcome!

1. Open an issue to start a discussion around a bug or a feature.
2. Fork the repository on GitHub and start making your changes to a new branch.
3. Write a test which shows that the bug was fixed.
4. Send a pull request. Make sure to add yourself to AUTHORS.


See also
--------

There are plenty other python email-around libraries:

 - premailer https://github.com/peterbe/premailer
 - pyzmail http://www.magiksys.net/pyzmail/
 - ...

.. image:: https://travis-ci.org/lavr/python-emails.png?branch=master
   :target: https://travis-ci.org/lavr/python-emails