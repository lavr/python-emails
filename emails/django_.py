# encoding: utf-8
from django.core.mail import get_connection
from .message import Message


class DjangoMessage(Message):

    """
    send via django email backend
    """

    _recipients = None

    def recipients(self):
        if self._recipients is not None:
            return self._recipients
        return [r[1] for r in self.mail_to]

    def send(self, mail_to=None, set_mail_to=True, mail_from=None,
             set_mail_from=False, context=None, connection=None, to=None):

        mail_to = mail_to or to  # "to" is legacy

        if mail_to is not None and set_mail_to:
            self.mail_to = mail_to
            self._recipients = None

        if not set_mail_to:
            self._recipients = [mail_to, ]

        if mail_from is not None and set_mail_from:
            self.mail_from = mail_from

        if context is not None:
            self.render(**context)

        connection = connection or get_connection()
        connection.send_messages([self, ])