from zope.interface import implements

from collective.subscribe.interfaces import IItemSubscriber


# MOCK COMMON:
DATA = {
            'name'  : u'Somebody',
            'user'  : 'somebody',
            'namespace' : 'member',
            }

DATAKEY = ('member', 'somebody')

class MockSub(object):
    implements(IItemSubscriber)
    def __init__(self):
        self.user = 'somebody'
        self.namespace = 'member'
        self.name = u'Somebody else'
        self.email = None
    def signature(self):
        if self.email and self.namespace == 'email':
            return ('email', self.email)
        return (self.namespace, self.user or self.email)

