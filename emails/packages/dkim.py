# This software is provided 'as-is', without any express or implied
# warranty.  In no event will the author be held liable for any damages
# arising from the use of this software.
# 
# Permission is granted to anyone to use this software for any purpose,
# including commercial applications, and to alter it and redistribute it
# freely, subject to the following restrictions:
# 
# 1. The origin of this software must not be misrepresented; you must not
#    claim that you wrote the original software. If you use this software
#    in a product, an acknowledgment in the product documentation would be
#    appreciated but is not required.
# 2. Altered source versions must be plainly marked as such, and must not be
#    misrepresented as being the original software.
# 3. This notice may not be removed or altered from any source distribution.
# 
# Copyright (c) 2008 Greg Hewgill http://hewgill.com

import base64
import hashlib
import re
import time

import sys, os.path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__))) # minihack for dnspython module
from dns import resolver as dns_resolver

__all__ = [
    "Simple",
    "Relaxed",
    "InternalError",
    "KeyFormatError",
    "MessageFormatError",
    "ParameterError",
    "sign",
    "verify",
]

class Simple:
    """Class that represents the "simple" canonicalization algorithm."""

    name = "simple"

    @staticmethod
    def canonicalize_headers(headers):
        # No changes to headers.
        return headers

    @staticmethod
    def canonicalize_body(body):
        # Ignore all empty lines at the end of the message body.
        return re.sub("(\r\n)*$", "\r\n", body)

class Relaxed:
    """Class that represents the "relaxed" canonicalization algorithm."""

    name = "relaxed"

    @staticmethod
    def canonicalize_headers(headers):
        # Convert all header field names to lowercase.
        # Unfold all header lines.
        # Compress WSP to single space.
        # Remove all WSP at the start or end of the field value (strip).
        return [(x[0].lower(), re.sub(r"\s+", " ", re.sub("\r\n", "", x[1])).strip()+"\r\n") for x in headers]

    @staticmethod
    def canonicalize_body(body):
        # Remove all trailing WSP at end of lines.
        # Compress non-line-ending WSP to single space.
        # Ignore all empty lines at the end of the message body.
        return re.sub("(\r\n)*$", "\r\n", re.sub(r"[\x09\x20]+", " ", re.sub("[\\x09\\x20]+\r\n", "\r\n", body)))

class DKIMException(Exception):
    """Base class for DKIM errors."""
    pass

class InternalError(DKIMException):
    """Internal error in dkim module. Should never happen."""
    pass

class KeyFormatError(DKIMException):
    """Key format error while parsing an RSA public or private key."""
    pass

class MessageFormatError(DKIMException):
    """RFC822 message format error."""
    pass

class ParameterError(DKIMException):
    """Input parameter error."""
    pass

def _remove(s, t):
    i = s.find(t)
    assert i >= 0
    return s[:i] + s[i+len(t):]

INTEGER = 0x02
BIT_STRING = 0x03
OCTET_STRING = 0x04
NULL = 0x05
OBJECT_IDENTIFIER = 0x06
SEQUENCE = 0x30

ASN1_Object = [
    (SEQUENCE, [
        (SEQUENCE, [
            (OBJECT_IDENTIFIER,),
            (NULL,),
        ]),
        (BIT_STRING,),
    ])
]

ASN1_RSAPublicKey = [
    (SEQUENCE, [
        (INTEGER,),
        (INTEGER,),
    ])
]

ASN1_RSAPrivateKey = [
    (SEQUENCE, [
        (INTEGER,),
        (INTEGER,),
        (INTEGER,),
        (INTEGER,),
        (INTEGER,),
        (INTEGER,),
        (INTEGER,),
        (INTEGER,),
        (INTEGER,),
    ])
]

def asn1_parse(template, data):
    """Parse a data structure according to ASN.1 template.

    @param template: A list of tuples comprising the ASN.1 template.
    @param data: A list of bytes to parse.

    """

    r = []
    i = 0
    for t in template:
        tag = ord(data[i])
        i += 1
        if tag == t[0]:
            length = ord(data[i])
            i += 1
            if length & 0x80:
                n = length & 0x7f
                length = 0
                for j in range(n):
                    length = (length << 8) | ord(data[i])
                    i += 1
            if tag == INTEGER:
                n = 0
                for j in range(length):
                    n = (n << 8) | ord(data[i])
                    i += 1
                r.append(n)
            elif tag == BIT_STRING:
                r.append(data[i:i+length])
                i += length
            elif tag == NULL:
                assert length == 0
                r.append(None)
            elif tag == OBJECT_IDENTIFIER:
                r.append(data[i:i+length])
                i += length
            elif tag == SEQUENCE:
                r.append(asn1_parse(t[1], data[i:i+length]))
                i += length
            else:
                raise KeyFormatError("Unexpected tag in template: %02x" % tag)
        else:
            raise KeyFormatError("Unexpected tag (got %02x, expecting %02x)" % (tag, t[0]))
    return r

def asn1_length(n):
    """Return a string representing a field length in ASN.1 format."""
    assert n >= 0
    if n < 0x7f:
        return chr(n)
    r = ""
    while n > 0:
        r = chr(n & 0xff) + r
        n >>= 8
    return r

def asn1_build(node):
    """Build an ASN.1 data structure based on pairs of (type, data)."""
    if node[0] == OCTET_STRING:
        return chr(OCTET_STRING) + asn1_length(len(node[1])) + node[1]
    if node[0] == NULL:
        assert node[1] is None
        return chr(NULL) + asn1_length(0)
    elif node[0] == OBJECT_IDENTIFIER:
        return chr(OBJECT_IDENTIFIER) + asn1_length(len(node[1])) + node[1]
    elif node[0] == SEQUENCE:
        r = ""
        for x in node[1]:
            r += asn1_build(x)
        return chr(SEQUENCE) + asn1_length(len(r)) + r
    else:
        raise InternalError("Unexpected tag in template: %02x" % node[0])

# These values come from RFC 3447, section 9.2 Notes, page 43.
HASHID_SHA1 = "\x2b\x0e\x03\x02\x1a"
HASHID_SHA256 = "\x60\x86\x48\x01\x65\x03\x04\x02\x01"

def str2int(s):
    """Convert an octet string to an integer. Octet string assumed to represent a positive integer."""
    r = 0
    for c in s:
        r = (r << 8) | ord(c)
    return r

def int2str(n, length = -1):
    """Convert an integer to an octet string. Number must be positive.

    @param n: Number to convert.
    @param length: Minimum length, or -1 to return the smallest number of bytes that represent the integer.

    """

    assert n >= 0
    r = []
    while length < 0 or len(r) < length:
        r.append(chr(n & 0xff))
        n >>= 8
        if length < 0 and n == 0: break
    r.reverse()
    assert length < 0 or len(r) == length
    return r

def rfc822_parse(message):
    """Parse a message in RFC822 format.

    @param message: The message in RFC822 format. Either CRLF or LF is an accepted line separator.

    @return Returns a tuple of (headers, body) where headers is a list of (name, value) pairs.
    The body is a CRLF-separated string.

    """

    headers = []
    lines = re.split("\r?\n", message)
    i = 0
    while i < len(lines):
        if len(lines[i]) == 0:
            # End of headers, return what we have plus the body, excluding the blank line.
            i += 1
            break
        if re.match(r"[\x09\x20]", lines[i][0]):
            headers[-1][1] += lines[i]+"\r\n"
        else:
            m = re.match(r"([\x21-\x7e]+?):", lines[i])
            if m is not None:
                headers.append([m.group(1), lines[i][m.end(0):]+"\r\n"])
            elif lines[i].startswith("From "):
                pass
            else:
                raise MessageFormatError("Unexpected characters in RFC822 header: %s" % lines[i])
        i += 1
    return (headers, "\r\n".join(lines[i:]))

def dnstxt(name):
    """Return a TXT record associated with a DNS name."""
    a = dns_resolver.query(name, dns.rdatatype.TXT)
    for r in a.response.answer:
        if r.rdtype == dns.rdatatype.TXT:
            return "".join(r.items[0].strings)
    return None

def fold(header):
    """Fold a header line into multiple crlf-separated lines at column 72."""
    i = header.rfind("\r\n ")
    if i == -1:
        pre = ""
    else:
        i += 3
        pre = header[:i]
        header = header[i:]
    while len(header) > 72:
        i = header[:72].rfind(" ")
        if i == -1:
            j = i
        else:
            j = i + 1
        pre += header[:i] + "\r\n "
        header = header[j:]
    return pre + header

def sign(message, selector, domain, privkey, identity=None, canonicalize=(Simple, Simple), include_headers=None, length=False, debuglog=None):
    """Sign an RFC822 message and return the DKIM-Signature header line.

    @param message: an RFC822 formatted message (with either \\n or \\r\\n line endings)
    @param selector: the DKIM selector value for the signature
    @param domain: the DKIM domain value for the signature
    @param privkey: a PKCS#1 private key in base64-encoded text form
    @param identity: the DKIM identity value for the signature (default "@"+domain)
    @param canonicalize: the canonicalization algorithms to use (default (Simple, Simple))
    @param include_headers: a list of strings indicating which headers are to be signed (default all headers)
    @param length: true if the l= tag should be included to indicate body length (default False)
    @param debuglog: a file-like object to which debug info will be written (default None)

    """

    (headers, body) = rfc822_parse(message)

    m = re.search("--\n(.*?)\n--", privkey, re.DOTALL)
    if m is None:
        raise KeyFormatError("Private key not found")
    try:
        pkdata = base64.b64decode(m.group(1))
    except TypeError as e:
        raise KeyFormatError(str(e))
    if debuglog is not None:
        print >>debuglog, " ".join("%02x" % ord(x) for x in pkdata)
    pka = asn1_parse(ASN1_RSAPrivateKey, pkdata)
    pk = {
        'version': pka[0][0],
        'modulus': pka[0][1],
        'publicExponent': pka[0][2],
        'privateExponent': pka[0][3],
        'prime1': pka[0][4],
        'prime2': pka[0][5],
        'exponent1': pka[0][6],
        'exponent2': pka[0][7],
        'coefficient': pka[0][8],
    }

    if identity is not None and not identity.endswith(domain):
        raise ParameterError("identity must end with domain")

    headers = canonicalize[0].canonicalize_headers(headers)

    if include_headers is None:
        include_headers = [x[0].lower() for x in headers]
    else:
        include_headers = [x.lower() for x in include_headers]
    sign_headers = [x for x in headers if x[0].lower() in include_headers]

    body = canonicalize[1].canonicalize_body(body)

    h = hashlib.sha256()
    h.update(body)
    bodyhash = base64.b64encode(h.digest())

    sigfields = [x for x in [
        ('v', "1"),
        ('a', "rsa-sha256"),
        ('c', "%s/%s" % (canonicalize[0].name, canonicalize[1].name)),
        ('d', domain),
        ('i', identity or "@"+domain),
        length and ('l', len(body)),
        ('q', "dns/txt"),
        ('s', selector),
        ('t', str(int(time.time()))),
        ('h', " : ".join(x[0] for x in sign_headers)),
        ('bh', bodyhash),
        ('b', ""),
    ] if x]
    sig = "DKIM-Signature: " + "; ".join("%s=%s" % x for x in sigfields)

    sig = fold(sig)

    if debuglog is not None:
        print >>debuglog, "sign headers:", sign_headers + [("DKIM-Signature", " "+"; ".join("%s=%s" % x for x in sigfields))]
    h = hashlib.sha256()
    for x in sign_headers:
        h.update(x[0])
        h.update(":")
        h.update(x[1])
    h.update(sig)
    d = h.digest()
    if debuglog is not None:
        print >>debuglog, "sign digest:", " ".join("%02x" % ord(x) for x in d)

    dinfo = asn1_build(
        (SEQUENCE, [
            (SEQUENCE, [
                (OBJECT_IDENTIFIER, HASHID_SHA256),
                (NULL, None),
            ]),
            (OCTET_STRING, d),
        ])
    )
    modlen = len(int2str(pk['modulus']))
    if len(dinfo)+3 > modlen:
        raise ParameterError("Hash too large for modulus")
    sig2 = int2str(pow(str2int("\x00\x01"+"\xff"*(modlen-len(dinfo)-3)+"\x00"+dinfo), pk['privateExponent'], pk['modulus']), modlen)
    sig += base64.b64encode(''.join(sig2))

    return sig + "\r\n"

def verify(message, debuglog=None):
    """Verify a DKIM signature on an RFC822 formatted message.

    @param message: an RFC822 formatted message (with either \\n or \\r\\n line endings)
    @param debuglog: a file-like object to which debug info will be written (default None)

    """

    (headers, body) = rfc822_parse(message)

    sigheaders = [x for x in headers if x[0].lower() == "dkim-signature"]
    if len(sigheaders) < 1:
        return False

    # Currently, we only validate the first DKIM-Signature line found.

    a = re.split(r"\s*;\s*", sigheaders[0][1].strip())
    if debuglog is not None:
        print >>debuglog, "a:", a
    sig = {}
    for x in a:
        if x:
            m = re.match(r"(\w+)\s*=\s*(.*)", x, re.DOTALL)
            if m is None:
                if debuglog is not None:
                    print >>debuglog, "invalid format of signature part: %s" % x
                return False
            sig[m.group(1)] = m.group(2)
    if debuglog is not None:
        print >>debuglog, "sig:", sig

    if 'v' not in sig:
        if debuglog is not None:
            print >>debuglog, "signature missing v="
        return False
    if sig['v'] != "1":
        if debuglog is not None:
            print >>debuglog, "v= value is not 1 (%s)" % sig['v']
        return False
    if 'a' not in sig:
        if debuglog is not None:
            print >>debuglog, "signature missing a="
        return False
    if 'b' not in sig:
        if debuglog is not None:
            print >>debuglog, "signature missing b="
        return False
    if re.match(r"[\s0-9A-Za-z+/]+=*$", sig['b']) is None:
        if debuglog is not None:
            print >>debuglog, "b= value is not valid base64 (%s)" % sig['b']
        return False
    if 'bh' not in sig:
        if debuglog is not None:
            print >>debuglog, "signature missing bh="
        return False
    if re.match(r"[\s0-9A-Za-z+/]+=*$", sig['bh']) is None:
        if debuglog is not None:
            print >>debuglog, "bh= value is not valid base64 (%s)" % sig['bh']
        return False
    if 'd' not in sig:
        if debuglog is not None:
            print >>debuglog, "signature missing d="
        return False
    if 'h' not in sig:
        if debuglog is not None:
            print >>debuglog, "signature missing h="
        return False
    if 'i' in sig and (not sig['i'].endswith(sig['d']) or sig['i'][-len(sig['d'])-1] not in "@."):
        if debuglog is not None:
            print >>debuglog, "i= domain is not a subdomain of d= (i=%s d=%d)" % (sig['i'], sig['d'])
        return False
    if 'l' in sig and re.match(r"\d{,76}$", sig['l']) is None:
        if debuglog is not None:
            print >>debuglog, "l= value is not a decimal integer (%s)" % sig['l']
        return False
    if 'q' in sig and sig['q'] != "dns/txt":
        if debuglog is not None:
            print >>debuglog, "q= value is not dns/txt (%s)" % sig['q']
        return False
    if 's' not in sig:
        if debuglog is not None:
            print >>debuglog, "signature missing s="
        return False
    if 't' in sig and re.match(r"\d+$", sig['t']) is None:
        if debuglog is not None:
            print >>debuglog, "t= value is not a decimal integer (%s)" % sig['t']
        return False
    if 'x' in sig:
        if re.match(r"\d+$", sig['x']) is None:
            if debuglog is not None:
                print >>debuglog, "x= value is not a decimal integer (%s)" % sig['x']
            return False
        if int(sig['x']) < int(sig['t']):
            if debuglog is not None:
                print >>debuglog, "x= value is less than t= value (x=%s t=%s)" % (sig['x'], sig['t'])
            return False

    m = re.match("(\w+)(?:/(\w+))?$", sig['c'])
    if m is None:
        if debuglog is not None:
            print >>debuglog, "c= value is not in format method/method (%s)" % sig['c']
        return False
    can_headers = m.group(1)
    if m.group(2) is not None:
        can_body = m.group(2)
    else:
        can_body = "simple"

    if can_headers == "simple":
        canonicalize_headers = Simple
    elif can_headers == "relaxed":
        canonicalize_headers = Relaxed
    else:
        if debuglog is not None:
            print >>debuglog, "Unknown header canonicalization (%s)" % can_headers
        return False

    headers = canonicalize_headers.canonicalize_headers(headers)

    if can_body == "simple":
        body = Simple.canonicalize_body(body)
    elif can_body == "relaxed":
        body = Relaxed.canonicalize_body(body)
    else:
        if debuglog is not None:
            print >>debuglog, "Unknown body canonicalization (%s)" % can_body
        return False

    if sig['a'] == "rsa-sha1":
        hasher = hashlib.sha1
        hashid = HASHID_SHA1
    elif sig['a'] == "rsa-sha256":
        hasher = hashlib.sha256
        hashid = HASHID_SHA256
    else:
        if debuglog is not None:
            print >>debuglog, "Unknown signature algorithm (%s)" % sig['a']
        return False

    if 'l' in sig:
        body = body[:int(sig['l'])]

    h = hasher()
    h.update(body)
    bodyhash = h.digest()
    if debuglog is not None:
        print >>debuglog, "bh:", base64.b64encode(bodyhash)
    if bodyhash != base64.b64decode(re.sub(r"\s+", "", sig['bh'])):
        if debuglog is not None:
            print >>debuglog, "body hash mismatch (got %s, expected %s)" % (base64.b64encode(bodyhash), sig['bh'])
        return False

    s = dnstxt(sig['s']+"._domainkey."+sig['d']+".")
    if not s:
        return False
    a = re.split(r"\s*;\s*", s)
    pub = {}
    for f in a:
        m = re.match(r"(\w+)=(.*)", f)
        if m is not None:
            pub[m.group(1)] = m.group(2)
        else:
            if debuglog is not None:
                print >>debuglog, "invalid format in _domainkey txt record"
            return False
    x = asn1_parse(ASN1_Object, base64.b64decode(pub['p']))
    # Not sure why the [1:] is necessary to skip a byte.
    pkd = asn1_parse(ASN1_RSAPublicKey, x[0][1][1:])
    pk = {
        'modulus': pkd[0][0],
        'publicExponent': pkd[0][1],
    }
    modlen = len(int2str(pk['modulus']))
    if debuglog is not None:
        print >>debuglog, "modlen:", modlen

    include_headers = re.split(r"\s*:\s*", sig['h'])
    if debuglog is not None:
        print >>debuglog, "include_headers:", include_headers
    sign_headers = []
    lastindex = {}
    for h in include_headers:
        i = lastindex.get(h, len(headers))
        while i > 0:
            i -= 1
            if h.lower() == headers[i][0].lower():
                sign_headers.append(headers[i])
                break
        lastindex[h] = i
    # The call to _remove() assumes that the signature b= only appears once in the signature header
    sign_headers += [(x[0], x[1].rstrip()) for x in canonicalize_headers.canonicalize_headers([(sigheaders[0][0], _remove(sigheaders[0][1], sig['b']))])]
    if debuglog is not None:
        print >>debuglog, "verify headers:", sign_headers

    h = hasher()
    for x in sign_headers:
        h.update(x[0])
        h.update(":")
        h.update(x[1])
    d = h.digest()
    if debuglog is not None:
        print >>debuglog, "verify digest:", " ".join("%02x" % ord(x) for x in d)

    dinfo = asn1_build(
        (SEQUENCE, [
            (SEQUENCE, [
                (OBJECT_IDENTIFIER, hashid),
                (NULL, None),
            ]),
            (OCTET_STRING, d),
        ])
    )
    if debuglog is not None:
        print >>debuglog, "dinfo:", " ".join("%02x" % ord(x) for x in dinfo)
    if len(dinfo)+3 > modlen:
        if debuglog is not None:
            print >>debuglog, "Hash too large for modulus"
        return False
    sig2 = "\x00\x01"+"\xff"*(modlen-len(dinfo)-3)+"\x00"+dinfo
    if debuglog is not None:
        print >>debuglog, "sig2:", " ".join("%02x" % ord(x) for x in sig2)
        print >>debuglog, sig['b']
        print >>debuglog, re.sub(r"\s+", "", sig['b'])
    v = int2str(pow(str2int(base64.b64decode(re.sub(r"\s+", "", sig['b']))), pk['publicExponent'], pk['modulus']), modlen)
    if debuglog is not None:
        print >>debuglog, "v:", " ".join("%02x" % ord(x) for x in v)
    assert len(v) == len(sig2)
    # Byte-by-byte compare of signatures
    return not [1 for x in zip(v, sig2) if x[0] != x[1]]

if __name__ == "__main__":
    message = """From: greg@hewgill.com\r\nSubject: test\r\n message\r\n\r\nHi.\r\n\r\nWe lost the game. Are you hungry yet?\r\n\r\nJoe.\r\n"""
    print(rfc822_parse(message))
    sig = sign(message, "greg", "hewgill.com", open("/home/greg/.domainkeys/rsa.private").read())
    print(sig)
    print(verify(sig+message))
    #print sign(open("/home/greg/tmp/message").read(), "greg", "hewgill.com", open("/home/greg/.domainkeys/rsa.private").read())
