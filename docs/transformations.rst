HTML transformer
----------------

Message HTML body usually should be modified before sent.

Base transformations, such as css inlining can be made by `Message.transform` method:

.. code-block:: python

    >>> message = emails.Message(html="<style>h1{color:red}</style><h1>Hello world!</h1>")
    >>> message.transform()
    >>> message.html
    u'<html><head></head><body><h1 style="color:red">Hello world!</h1></body></html>'

`Message.transform` can take some arguments with speaken names `css_inline`, `remove_unsafe_tags`,
`make_links_absolute`, `set_content_type_meta`, `update_stylesheet`, `images_inline`.

More specific transformation can be made via `transformer` property.

Example of custom link transformations:

.. code-block:: python

    >>> message = emails.Message(html="<img src='promo.png'>")
    >>> message.transformer.apply_to_images(func=lambda src, **kw: 'http://mycompany.tld/images/'+src)
    >>> message.transformer.save()
    >>> message.html
    u'<html><body><img src="http://mycompany.tld/images/promo.png"></body></html>'

Example of customized making images inline:

.. code-block:: python

    >>> message = emails.Message(html="<img src='promo.png'>")
    >>> message.attach(filename='promo.png', data=open('promo.png', 'rb'))
    >>> message.attachments['promo.png'].is_inline = True
    >>> message.transformer.synchronize_inline_images()
    >>> message.transformer.save()
    >>> message.html
    u'<html><body><img src="cid:promo.png"></body></html>'


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
