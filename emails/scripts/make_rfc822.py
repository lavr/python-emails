#!/usr/bin/env python
# coding: utf-8

"""

Simple utility that imports html from url ang print generated rfc822 message to console.

Example usage:

    $ python make_rfc822.py --url=http://lavr.github.io/python-emails/tests/campaignmonitor-samples/sample-template/template-widgets.html
            --subject="Some subject"
            --from-name="Sergey Lavrinenko"
            --from-email=s@lavr.me
            --message-id-domain=localhost
            --send-test-email-to=sergei-nko@mail.ru
            --smtp-host=mxs.mail.ru
            --smtp-port=25

Copyright 2013  Sergey Lavrinenko <s@lavr.me>

"""

import os
from optparse import OptionParser
import sys
import logging

import emails

def real_main(options):

    if options.message_id_domain:
        message_id = emails.utils.MessageID(domain=options.message_id_domain)
    else:
        message_id = None

    loader = emails.loader.from_url(url=options.url, images_inline=options.inline_images)

    message = emails.Message.from_loader(loader=loader,
                          headers={'X-Imported-From-URL': options.url },
                          mail_from = (options.from_name, options.from_email),
                          subject=options.subject,
                          message_id=message_id
                        )

    if options.send_test_email_to:
        print __name__, "options.send_test_email_to YES"

        smtp_params = {}
        for k in ('host', 'port', 'ssl', 'user', 'password', 'debug'):
            smtp_params[k] = getattr(options, 'smtp-%s' % k, None)

        for mail_to in options.send_test_email_to.split(','):
            r = message.send(to=mail_to, smtp=smtp_params)
            print __name__, "mail_to=", mail_to, "result=", r, r.error
            if r.error:
                raise r.error

    if options.output_format=='eml':
        print message.as_string()
    else:
        print message.html_body

if __name__=="__main__":

    usage = "usage: %prog [options]"

    parser = OptionParser(usage=usage)

    parser.add_option("-u", "--url", dest="url", default=None)
    parser.add_option("-f", "--from-email", dest="from_email", default=None)
    parser.add_option("-n", "--from-name", dest="from_name", default=None)
    parser.add_option("-s", "--subject", dest="subject", default=None)
    parser.add_option("", "--message-id-domain", dest="message_id_domain", default=None)
    parser.add_option("", "--inline-images", action="store_true", dest="inline_images", default=False)
    parser.add_option("", "--log-level", dest="log_level", default="debug")
    parser.add_option("", "--send-test-email-to", dest="send_test_email_to", default=None)
    parser.add_option("", "--output-format", dest="output_format", default='eml')

    parser.add_option("", "--smtp-host", dest="smtp_host", default="localhost")
    parser.add_option("", "--smtp-port", dest="smtp_port", default="25")
    parser.add_option("", "--smtp-ssl", dest="smtp_ssl", action="store_true")
    parser.add_option("", "--smtp-user", dest="smtp_user", default=None)
    parser.add_option("", "--smtp-password", dest="smtp_password", default=None)
    parser.add_option("", "--smtp-debug", dest="smtp_debug", action="store_true")

    (options, args) = parser.parse_args()

    logging.basicConfig( level=logging.getLevelName(options.log_level.upper()) )
    real_main(options)