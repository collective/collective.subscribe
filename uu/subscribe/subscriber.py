import persistent
from zope.interface import implements
from zope import schema

from uu.subscribe.interfaces import IItemSubscriber
from uu.subscribe.utils import bind_field_properties


class ItemSubscriber(persistent.Persistent):
    """Item subscriber implementation"""
    
    implements(IItemSubscriber)
    
    bind_field_properties(locals(), IItemSubscriber)

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

