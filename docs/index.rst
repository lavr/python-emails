python-emails
=============

.. module:: emails

Modern email handling in python.

.. code-block:: python

    m = emails.Message(html=T("<html><p>Build passed: {{ project_name }} <img src='cid:icon.png'> ..."),
                       text=T("Build passed: {{ project_name }} ..."),
                       subject=T("Passed: {{ project_name }}#{{ build_id }}"),
                       mail_from=("CI", "ci@mycompany.com"))
    m.attach(filename="icon.png", content_disposition="inline", data=open("icon.png", "rb"))
    response = m.send(render={"project_name": "user/project1", "build_id": 121},
                      to='somebody@mycompany.com',
                      smtp={"host":"mx.mycompany.com", "port": 25})

    if response.status_code not in [250, ]:
        # message is not sent, retry later
        ...

See `the same code, without Emails <https://gist.github.com/lavr/fc1972c125ccaf4d4b91>`_.

Emails code is not much simpler than `the same code in django <https://gist.github.com/lavr/08708b15d33fc2ad718b>`_,
but it is still more elegant, can be used in django environment and has html transformation methods
(see ``HTML Transformer`` section).


.. include:: examples.rst

.. include:: transformations.rst

.. include:: install.rst

.. include:: todo.rst

.. include:: howtohelp.rst

.. include:: links.rst
