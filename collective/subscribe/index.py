from persistent import Persistent
from zope.interface import implements
from zope.schema.fieldproperty import FieldProperty
from BTrees.OOBTree import OOBTree, OOSet

from collective.subscribe.interfaces import ISubscriptionIndex, IItemSubscriber


def _validate_signature(sig):
    """validate signature is signature tuple, two items, both strings"""
    if not isinstance(sig, tuple):
        raise ValueError('subscriber signature must be tuple')
    if len(sig) != 2:
        raise ValueError('subscriber signature must be two items')
    if not (isinstance(sig[0], str) and isinstance(sig[1], str)):
        raise ValueError('subscriber signature elements must be strings')

class ItemUIDToSignatureMapping(OOBTree):
    """
    OOBTree that validates keys as uid strings.
    
    Does not validate values.
    """
    
    def __setitem__(self, key, value):
        if not isinstance(key, basestring):
            raise ValueError('Subscription index: key must be UID string')
        elif isinstance(key, unicode):
            key = key.encode('utf-8')
        super(ItemUIDToSignatureMapping, self).__setitem__(key, value)


class SignatureToItemUIDMapping(OOBTree):
    """
    OOBTree that validates keys as subscriber signature tuples. 

    Does not validate values.
    """
    
    def __setitem__(self, key, value):
        _validate_signature(key)
        super(SignatureToItemUIDMapping, self).__setitem__(key, value)


class SubscriptionIndex(Persistent):
    """
    Subscription index maintains forward/reverse index mappings between
    item UID strings and subscriber signature tuples.
    """
    implements(ISubscriptionIndex)
    
    name = FieldProperty(ISubscriptionIndex['name'])
    
    def __init__(self, name):
        if isinstance(name, unicode):
            name = name.encode('utf-8')
        self.name = name
        self._forward = ItemUIDToSignatureMapping()
        self._reverse = SignatureToItemUIDMapping()

    def _normalize_subscriber(self, sub):
        """normalize subscriber or signature to signature"""
        if IItemSubscriber.providedBy(sub):
            sub = sub.signature()
        _validate_signature(sub)
        return sub
    
    def index(self, subscriber, item_uid):
        """
        Given an subscriber and and item_uid, associate for this index in
        both (subscriber to items) and (item to subscribers) mappings.

        The subscriber argument can be either a two-item tuple key or
        an IItemSubsriber object, in which case the key will be extracted
        by calling the signature() method of the subscriber.
        """
        # normalize key/value
        signature = self._normalize_subscriber(subscriber)
        item_uid = str(item_uid)
        
        # forward index
        if item_uid not in self._forward:
            self._forward[item_uid] = OOSet()
        subscribers_for_item = self._forward[item_uid]
        if signature not in subscribers_for_item:
            subscribers_for_item.insert(signature)
        
        # reverse index
        if signature not in self._reverse:
            self._reverse[signature] = OOSet()
        items_for_subscriber = self._reverse[signature]
        if item_uid not in items_for_subscriber:
            items_for_subscriber.insert(item_uid)
        

    
    def unindex(self, subscriber, item_uid):
        """
        Given an subscriber and item_uid, remove any associations in this
        index between them.
        
        The subscriber argument can be either a two-item tuple key or
        an IItemSubsriber object, in which case the key will be extracted
        by calling the signature() method of the subscriber.
        """
        # normalize key/value
        signature = self._normalize_subscriber(subscriber)
        item_uid = str(item_uid)
        
        # remove any association from forward index, if found
        if item_uid in self._forward:
            subscribers_for_item = self._forward[item_uid]
            if signature in subscribers_for_item:
                subscribers_for_item.remove(signature)
        
        # remove from reverse index, if found:
        if signature in self._reverse:
            items_for_subscriber = self._reverse[signature]
            if item_uid in items_for_subscriber:
                items_for_subscriber.remove(item_uid)
            
    def item_uids_for(self, subscriber):
        """
        Find, return tuple of item UIDs given a subscriber for this index.
        
        The subscriber argument can be either a two-item tuple key or
        an IItemSubsriber object, in which case the key will be extracted
        by calling the signature() method of the subscriber.        
        """
        signature = self._normalize_subscriber(subscriber)
        if signature not in self._reverse:
            return ()
        return tuple(self._reverse[signature]) #iterate items/sub -> tuple
    
    def subscribers_for(self, item_uid):
        """
        Given an item UID, find and return a tuple of subscriber signatures
        (composed keys) for subscribers an item in this index.
        """
        item_uid = str(item_uid)
        if item_uid not in self._forward:
            return ()
        return tuple(self._forward[item_uid]) #iterate subs/item -> tuple


