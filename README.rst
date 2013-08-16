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
                          from=('Company Team', 'contact@mycompany.com'))


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
                          html=T('<p>Dear {{account}} owner! This is a receipt for your subscription...'),
                          from=('ABC', 'robot@mycompany.com'))

    message.send(to=('John Braun', 'jbraun@gmail.com'), render={'account': 'lavr', 'no':'141051906163'} )

Send without pain:

::

    SMTP = { 'host':'smtp.mycompany.com', 'port': 465, 'ssl': True }
    r = messages.send(to=('John Braun', 'jbraun@gmail.com'), smtp=SMTP)




One more thing
--------------

Module ships with email-from-html loader. Your designers will love for this:

::

    import emails
    URL = 'http://_youproject_.github.io/newsletter/2013-08-14/index.html'
    page = emails.loader.from_url(URL, css_inline=True, make_links_absolute=True)
    message = emails.html(html=page.html, ...)
    for mail_to in _get_maillist():
        message.send(to=mail_to)


Features
--------

-  Internationalization & Unicode bodies
-  DKIM signatures
-  HTML page loader & CSS inliner
-  Body and attachments http import
-  Body & headers preprocessors

TODO
-----
- Fix all bugs
- More genius css inliner
- (may be) ESP integration: amazon ses, sendgrid, ...



How to Help
-----------

Module is under development and contributions are welcome!

1. Open an issue to start a discussion around a bug or a feature.
2. Fork the repository on GitHub and start making your changes to a new branch.
3. Write a test which shows that the bug was fixed.
4. Send a pull request. Make sure to add yourself to AUTHORS.


Background
----------

Library inspired by python-requests and werkzeug. Much based on mailcube.ru experience.


.. image:: https://travis-ci.org/lavr/python-emails.png?branch=master
   :target: https://travis-ci.org/lavr/python-emails