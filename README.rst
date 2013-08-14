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
    page = emails.loader.load_url(URL, css_inline=True, make_links_absolute=True)
    message = emails.html(html=page.html, ...)
    for mail_to in _get_maillist():
        message.send(to=mail_to)


Features
--------

-  Internationalization & Unicode bodies
-  DKIM signatures
-  CSS inliner
-  Body and attachments http import
-  Body & headers preprocessors
-  (TODO) ESP integration: amazon ses, sendgrid


Thanks
------

Library is mush based on mailcube.ru experience.
Inspired by python-requests and werkzeug.


.. image:: https://travis-ci.org/lavr/python-emails.png?branch=master   :target: https://travis-ci.org/lavr/python-emails