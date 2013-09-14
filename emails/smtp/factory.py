# encoding: utf-8

from .backend import SMTPBackend

def _serialize_dict(d):
    # simple dict serializer
    r = []
    for (k, v) in d.items():
        r.append("%s=%s" % (k, v))
    return ";".join(r)


class SMTPConnectionFactory:

    smtp_cls = SMTPBackend

    def __init__(self):
        self.pool = {}

    def __getitem__(self, k):

        if not isinstance(k, dict):
            raise ValueError("item must be dict, not %s" % type(k))

        kk = _serialize_dict(k)

        r = self.pool.get(kk, None)

        if r is None:
            r = self.smtp_cls(**k)
            self.pool[kk] = r

        return r

    def reconnect(self, k):

        kk = _serialize_dict(k)

        if kk in self.pool:
            del self.pool[kk]

        return self[k]