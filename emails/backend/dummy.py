# encoding: utf-8

class DummyBackend(object):

    def sendmail(self, from_addr, to_addrs, msg, mail_options=[], rcpt_options=[]):
        pass