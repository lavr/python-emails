python-emails
=============

Emails without pain for python.


What can you do:
----------------

Create message:

::

    import emails
    message = emails.html(html=open('letter.html'),
                          subject='Friday party',
                          mail_from=('Company Team', 'contact@mycompany.com'))


Attach files or inline images:

::

    message.attach( data=open('event.ics'), filename='Event.ics' )
    message.attach( data=open('image.png'), filename='image.png', content_disposition='inline' )

Add DKIM easily:

::

    message.dkim( key=open('my.key'), domain='mycompany.com', selector='newsletter' )



Templating:

::

    from emails.template import JinjaTemplate as T

    message = emails.html(subject=T('Payment Receipt No.{{no}}'),
                          html=T('<p>Dear {{ name }}! This is a receipt for your subscription...'),
                          mail_from=('ABC', 'robot@mycompany.com'))

    message.send(to=('John Brown', 'jbrown@gmail.com'), render={'name': 'John Brown', 'billno':'141051906163'} )

Send without pain and (even) get response:

::

    SMTP = { 'host':'smtp.mycompany.com', 'port': 465, 'ssl': True }
    r = message.send(to=('John Brown', 'jbrown@gmail.com'), smtp=SMTP)
    assert r.status_code == 250




One more thing
--------------

Library ships with fairy email-from-html loader.
Design email with less pain or even let designers make design:

::

    import emails
    URL = 'http://_youproject_.github.io/newsletter/2013-08-14/index.html'
    page = emails.loader.from_url(URL, css_inline=True, make_links_absolute=True)
    message = emails.html(html=page.html, ...)
    for mail_to in _get_maillist():
        message.send(to=mail_to)

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


Features
--------

-  Internationalization & Unicode bodies
-  DKIM signatures
-  HTML page loader & CSS inliner
-  Body and attachments http import
-  Body & headers preprocessors

TODO
----
- Python3 (almost done)
- Add "safety stuff" from django (done)
- Django integration (django.core.mail.backends.smtp.EmailBackend subclass)
- Flask extension
- Documentation
- 100% test coverage
- More accurate smtp session handling
- Some patches for pydkim performance (i.e. preload key once, not each time)
- More genius css inliner
- Catch all bugs
- ESP integration: Amazon SES, SendGrid, ...
- deb package (ubuntu package done)
- rpm package

How to Help
-----------

Library is under development and contributions are welcome!

1. Open an issue to start a discussion around a bug or a feature.
2. Fork the repository on GitHub and start making your changes to a new branch.
3. Write a test which shows that the bug was fixed.
4. Send a pull request. Make sure to add yourself to AUTHORS.


Background
----------

API structure inspired by python-requests and werkzeug libraries.
Some code is from my mailcube.ru experience.


See also
--------

There are plenty other python email-around libraries:

 - premailer https://github.com/peterbe/premailer
 - pyzmail http://www.magiksys.net/pyzmail/
 - ...

.. image:: https://travis-ci.org/lavr/python-emails.png?branch=master
   :target: https://travis-ci.org/lavr/python-emails