import persistent
from zope.interface import implements
from BTrees.OOBTree import OOBTree
from BTrees.Length import Length

from collective.subscribe.interfaces import IItemSubscriber, ISubscribers
from collective.subscribe.utils import bind_field_properties


class ItemSubscriber(persistent.Persistent):
    """Item subscriber implementation"""
    
    implements(IItemSubscriber)
    
    bind_field_properties(locals(), IItemSubscriber) #props from field schema

    def __init__(self, **kwargs):
        """
        Construct, if keyword arguments are used to construct, validate
        invariant on passed field values.
        """
        if kwargs:
            user = kwargs.get('user', None)
            name = kwargs.get('name', None)
            namespace = kwargs.get('namespace', 'member')
            email = kwargs.get('email', None)
            if isinstance(user, unicode):
                user = user.encode('utf-8')
            self.user = user
            if isinstance(email, unicode):
                email = email.encode('utf-8')
            self.email = email
            if isinstance(name, str):
                name = name.decode('utf-8')
            self.name = name
            if isinstance(namespace, unicode):
                namespace = namespace.encode('utf-8')
            self.namespace = namespace
            IItemSubscriber.validateInvariants(self)
    
    def signature(self):
        """
        return two-string tuple signature of (namespace, user or email); can
        be used as a composed key for storage implementations.  Raises a 
        zope.interface.Invalid exception if signature is not possible due to
        insufficient field data.
        """
        IItemSubscriber.validateInvariants(self) #may raise Invalid...
        namespace = self.namespace
        identifier = self.user
        if self.email and not self.user:
            namespace = 'email'     #ignore field default
            identifier = self.email
        return (namespace, identifier)


class SubscribersContainer(OOBTree):
    """Container/mapping for subscribers"""
    implements(ISubscribers)
    
    def __init__(self, *args, **kwargs):
        super(SubscribersContainer, self).__init__(*args, **kwargs)
        self.size = Length()
    
    # wrap superclass __getstate__ and __setstate__ to save attrs such

    def __getstate__(self):
        tree_state = super(SubscribersContainer, self).__getstate__()
        attr_state = [(k,v) for k,v in self.__dict__.items()
                      if not (k.startswith('_v_') or k.startswith('__'))]
        return (tree_state, attr_state)
    
    def __setstate__(self, v):
        tree_state = v[0]
        attr_state = v[1]
        for k,v in attr_state:
            setattr(self, k, v)
        super(SubscribersContainer, self).__setstate__(tree_state)
    
    def _normalize_key(self, key):
        """
        given key or object providing IItemSubscriber, normalize unique key
        """
        if IItemSubscriber.providedBy(key):
            key = key.signature()
        elif isinstance(key, basestring):
            key = ('email', str(basestring))
        if not (len(key) == 2 and key[0] and key[1]):
            raise KeyError('incomplete key for subscriber')
        return key
    
    def _set_new(self, key, value):
        """set new item, but do not allow replacing existing item"""
        if key in self:
            raise ValueError('attempt to add: duplicate key; record exists')
        self.__setitem__(key, value)
    
    def add(self, *args, **kwargs):
        k = None
        fields = kwargs
        if not kwargs and len(args)==1:
            v = args[0]
            if IItemSubscriber.providedBy(v):
                k = self._normalize_key(v)
                if isinstance(v, persistent.Persistent):
                    self._set_new(k, v)
                    return k, v
                fields = v.__dict__ # we'll copy values, not object to store
            # otherwise, assume a dict from args[0]:
            else:
                try:
                    fields = dict(v)
                except ValueError:
                    import sys
                    exc_info = sys.exc_info()
                    raise KeyError, exc_info[1], exc_info[2]
        v = ItemSubscriber(**fields)
        if k is None:
            k = self._normalize_key(v)
        self._set_new(k, v)
        return k, v
    
    # Callers should not use __setitem__ -- it is here as a check
    # on keeping a BTree size/length extrinsic to the BTree itself.
    def __setitem__(self, key, value):
        if not IItemSubscriber.providedBy(value):
            raise ValueError('__setitem__ value must provide IItemSubscriber')
        if key not in self:
            self.size.change(1) #increment
        super(SubscribersContainer, self).__setitem__(key, value)
    
    def get(self, subscriber, default=None):
        key = self._normalize_key(subscriber)
        return super(SubscribersContainer, self).get(key, default)
    
    def __getitem__(self, key):
        key = self._normalize_key(key)
        return super(SubscribersContainer, self).__getitem__(key)
    
    def __len__(self):
        return self.size()
    
    def __contains__(self, key):
        normalized = self._normalize_key(key)
        if IItemSubscriber.providedBy(key):
            if key is not super(SubscribersContainer, self).get(normalized,
                                                                None):
                return False
        key = self._normalize_key(normalized)
        return super(SubscribersContainer, self).__contains__(normalized)
    
    def __delitem__(self, key):
        key = self._normalize_key(key)
        super(SubscribersContainer, self).__delitem__(key)
        self.size.change(-1) #decrement if superclass __delitem__ succeeds

