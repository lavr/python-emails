Python-emails
=============

Try to make humanistic library for email creation in python.

Based on mailcube.ru experience. Inspired by python-requests and
werkzeug. Contribute from django, lamson.

What we'll get
--------------

::

    message = emails.html(html=open('letter.html'),
                          subject='Friday party',
                          from=('Company Team', 'contact@mycompany.com'))

    message.attach( data=open('event.ics'), filename='Event.ics' )

    message.dkim( key=open('my.key'), domain='mycompany.com', selector='newsletter' )

    r = messages.send(to=('John Braun', 'jbraun@gmail.com'))



Features
--------

-  Internationalization & Unicode bodies
-  DKIM signatures
-  CSS inliner
-  Body and attachments http import
-  Body & headers preprocessors
-  (may be) ESP integration: amazon ses, sendgrid

