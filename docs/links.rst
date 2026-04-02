See also
========

Alternatives
------------

There are several Python libraries for sending email, each with a different focus:

- **smtplib + email** (standard library) — built into Python, provides low-level SMTP
  transport and RFC-compliant message construction. Full control, but requires manual
  MIME assembly for HTML emails with attachments. python-emails builds on top of these
  modules and adds a higher-level API with HTML transformations, template support, and
  loaders.

- `yagmail <https://github.com/kootenpv/yagmail>`_ — a friendly Gmail/SMTP client that
  auto-detects content types and simplifies sending. Supports OAuth2 for Gmail and
  optional DKIM signing. A good choice when you need a quick way to send emails with
  minimal setup.

- `red-mail <https://github.com/Miksus/red-mail>`_ — advanced email sending with
  built-in Jinja2 templates, prettified HTML tables, and embedded images. A good fit
  if you need to send data-driven reports.

- `envelope <https://github.com/CZ-NIC/envelope>`_ — an all-in-one library with GPG
  and S/MIME encryption, a fluent Python API, and a CLI interface. The right choice when
  email encryption or signing is a requirement.

python-emails focuses on **HTML email as a first-class citizen**: loading HTML from
URLs, files, ZIP archives, or directories, automatic CSS inlining and image embedding
via built-in transformations, and multiple template engines (Jinja2, Mako, string
templates). It also provides DKIM signing and Django integration out of the box.


Acknowledgements
----------------

python-emails uses `premailer <https://github.com/peterbe/premailer>`_ for CSS inlining
— converting ``<style>`` blocks into inline ``style`` attributes for maximum email client
compatibility.
