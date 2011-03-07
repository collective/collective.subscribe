from persistent import Persistent
from persistent.dict import PersistentDict
from zope.interface import implements
from BTrees.OOBTree import OOBTree

from uu.subscribe.interfaces import ISubscriptionCatalog, ISubscriptionIndex
from uu.subscribe.interfaces import IItemResolver, IItemSubscriber
from uu.subscribe.index import SubscriptionIndex


class SubscriptionIndexCollection(OOBTree):
    def __setitem__(self, key, value):
        key = str(key)
        if not ISubscriptionIndex.providedBy(value):
            raise ValueError('indexes colllection value must be index')
        super(SubscriptionIndexCollection, self).__setitem__(key, value)


class SubscriptionCatalog(Persistent):
    """Subscription catalog"""

    implements(ISubscriptionCatalog)

    def __init__(self):
        self.metadata = OOBTree()
        self.indexes = SubscriptionIndexCollection()
    
    def _search_for_items(self, query):
        result = None
        for (k,v) in query.items():
            if str(k) in self.indexes:
                idx = self.indexes[str(k)]
                if IItemSubscriber.providedBy(v):
                    signature = v.signature()
                elif isinstance(v, tuple) and len(v) == 2:
                    signature = v
                else:
                    raise ValueError('unable to obtain subscriber signature')
                if result is None:
                    result = set(idx.item_uids_for(signature))
                else:
                    result = result & set(idx.item_uids_for(signature))
        if not result:
            return ()
        return tuple(result)
    
    def _search_for_subscribers(self, query):
        result = None
        for (k,v) in query.items():
            if str(k) in self.indexes:
                idx = self.indexes[str(k)]
                uid = str(v)
                if result is None:
                    result = set(idx.subscribers_for(uid))
                else:
                    result = result & set(idx.subscribers_for(uid))
        if not result:
            return ()
        return tuple(result)
        
    def search(self, query):
        k, v = query.items()[0]
        if IItemSubscriber.providedBy(v) or isinstance(v, tuple):
            return self._search_for_items(query) #tuple of uids
        return self._search_for_subscribers(query)
    
    def index(self, subscriber, uid, names):
        if isinstance(names, basestring):
            names = (str(names),)
        for name in names:
            if name not in self.indexes:
                self.indexes[name] = SubscriptionIndex(name)
            idx = self.indexes[name]
            idx.index(subscriber, uid)
    
    def unindex(self, subscriber, uid, names):
        if isinstance(names, basestring):
            names = (str(names),)
        for name in names:
            if name in self.indexes:
                idx = self.indexes[name]
                idx.unindex(subscriber, uid)
    
    def get_item(self, uid):
        if not hasattr(self, '_v_resolver'):
            self._v_resolver = queryUtility(IItemResolver)
        return self._v_resolver(uid)
    
    def get_subscriber(self, signature):
        if not hasattr(self, '_v_container'):
            self._v_container = queryUtility(ISubscribers)
        return self._v_container.get(signature, None)
