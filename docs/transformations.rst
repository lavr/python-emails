HTML transformer
----------------

Message HTML body can be modified with 'transformer' object:

.. code-block:: python

    >>> message = emails.Message(html="<img src='promo.png'>")
    >>> message.transformer.apply_to_images(func=lambda src, **kw: 'http://mycompany.tld/images/'+src)
    >>> message.transformer.save()
    >>> message.html
    u'<html><body><img src="http://mycompany.tld/images/promo.png"></body></html>'

Code example to make images inline:

.. code-block:: python

    >>> message = emails.Message(html="<img src='promo.png'>")
    >>> message.attach(filename='promo.png', data=open('promo.png', 'rb'))
    >>> message.attachments['promo.png'].is_inline = True
    >>> message.transformer.synchronize_inline_images()
    >>> message.transformer.save()
    >>> message.html
    u'<html><body><img src="cid:promo.png"></body></html>'

To inline CSS using `Premailer <https://github.com/peterbe/premailer>`_:

.. code-block:: python

    >>> html = '''<style>h1 { color: red }</style>
    ...           <h1>Hello world!</h1>'''
    >>> message = emails.Message(html=html)
    >>> message.transformer.premailer.transform()
    >>> message.transformer.save()
    >>> print(message.html)
    <html><head/><body><h1 style="color:red">Hello world!</h1></body></html>


Loaders
-------

python-emails ships with couple of loaders.

Load message from url:

.. code-block:: python

    import emails.loader
    message = emails.loader.from_url(url="http://xxx.github.io/newsletter/2015-08-14/index.html")


Load from zipfile or directory:

.. code-block:: python

    message = emails.loader.from_zipfile(open('design_pack.zip', 'rb'))
    message = emails.loader.from_directory('/home/user/design_pack')

Zipfile and directory loaders require at least one html file (with "html" extension).
