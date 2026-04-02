Install
=======

Install from pypi:

.. code-block:: bash

    $ pip install emails

This installs the lightweight core for building and sending email messages.

To use HTML transformation features (CSS inlining, image embedding, loading from URL/file):

.. code-block:: bash

    $ pip install "emails[html]"

To use Jinja2 templates (the ``T()`` shortcut):

.. code-block:: bash

    $ pip install "emails[jinja]"

To use async sending (``send_async()``):

.. code-block:: bash

    $ pip install "emails[async]"
