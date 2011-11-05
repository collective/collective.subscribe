from hashlib import md5
from base64 import urlsafe_b64encode as encode

from zope.interface import implements
from BTrees.OOBTree import OOBTree

from collective.subscribe.interfaces import ISubscriptionKeys
from collective.subscribe.utils import valid_signature


# string form of tuple delimited by slashes, sub. sig. is numeric hash
pathform = lambda name, sig, uid: '%s/%s/%s' % (name, hash(sig), uid)
# md5 digest of string form:
mkhash = lambda name, sig, uid: md5(pathform(name,sig,uid)).digest()
# base64 encoding of md5 is URL-safe with last two bytes of padding removed:
mkkey = lambda name, sig, uid: encode(mkhash(name,sig,uid))[:22]


class SubscriptionKeys(OOBTree):
    """Mapping of string keys to (name, subscriber signature, uid)"""
    implements(ISubscriptionKeys)
    
    key_description = u"Base64 encoded (trailing padding removed) md5 hash "\
                      u"of a slash-delimited string containing the "\
                      u"subscription name, long-integer hash of subscriber "\
                      u"signature tuple, and item uid of subscribed content."
    
    def generate(self, name, signature, uid):
        return mkkey(name, signature, uid)
    
    def _validate(self, value):
        if not (hasattr(value, '__len__') and hasattr(value, '__iter__')):
            raise ValueError('Value must be iterable')
        if not len(value) == 3:
            raise ValueError('Value must have length of exactly 3 elements')
        if not valid_signature(value[1]):
            raise ValueError('Invalid subscriber signature.')
        if not (isinstance(value[0], str) and isinstance(value[2], str)):
            raise ValueError('Invalid subscription description tuple.')
    
    def add(self, name, signature, uid):
        """
        Add item to container/mapping as value using generated key, 
        return that key.  Validates, does not check for duplicates or
        existing entries.  Returns generated key.
        """
        self._validate((name, signature, uid))
        key = mkkey(name, signature, uid)
        self[key] = (name, signature, uid)
        return key
    
    def __setitem__(self, key, value):
        """set item with validation of key, values"""
        if not isinstance(key, basestring):
            raise KeyError('Subscription key must be string')
        self._validate(value)
        super(SubscriptionKeys, self).__setitem__(str(key), tuple(value))

