
import sys
import unittest2 as unittest
from new import instancemethod as methodtype

import persistent
from zope.interface import Invalid, implements
from zope.schema import getSchemaValidationErrors, ValidationError

from collective.subscribe.interfaces import IItemSubscriber, ISubscribers
from collective.subscribe.subscriber import ItemSubscriber, SubscribersContainer
from collective.subscribe.tests.common import DATA, DATAKEY, MockSub


class TestSubscriber(unittest.TestCase):
    """Test subscriber entity implementation and interface assumptions"""
    
    def fail_on_err(self, exc, f, *args, **kwargs):
        try:
            f(*args, **kwargs)
        except exc:
            self.addFailure(
                'raises exception incorrectly',
                sys.exc_info())
    
    def test_invariants(self):
        """Test interface invariants for IItemSubscriber"""
        verify = lambda sub: IItemSubscriber.validateInvariants(sub)
        # test empty email and user
        subscriber = ItemSubscriber()
        self.assertRaises(Invalid, verify, subscriber)
        # test email only
        subscriber.email = 'jdoe@example.com'
        self.fail_on_err(Invalid, verify, subscriber)
        # test both user and email
        subscriber.user = 'jane.doe'
        self.fail_on_err(Invalid, verify, subscriber)
        # test user only
        subscriber.email = None
        self.fail_on_err(Invalid, verify, subscriber)
    
    def test_defaults(self):
        """Test required and any default values"""
        subscriber = ItemSubscriber()
        self.assertIsNone(subscriber.email)
        self.assertIsNone(subscriber.user)
        self.assertIsNone(subscriber.name)
        self.assertEqual(subscriber.namespace, 'member')
        # now that we have verified defaults, validate all fields
        self.fail_on_err(ValidationError,
            getSchemaValidationErrors,
            IItemSubscriber,
            subscriber)
    
    def test_signature(self):
        key1 = ('email', 'me@example.com')
        sub1 = ItemSubscriber()
        self.assertRaises(Invalid, sub1.signature) #no email, no user
        sub1.email = 'me@example.com'
        assert sub1.signature() == key1
        key2 = ('member', 'here')
        sub2 = ItemSubscriber()
        sub2.user = 'here' #default namespace is 'member'
        assert sub2.signature() == key2
    
    def test_construction(self):
        """Test different construction parameters for subscriber"""
        subscriber = ItemSubscriber()
        self.assertIsNone(subscriber.email)
        self.assertIsNone(subscriber.user)
        self.assertIsNone(subscriber.name)
        self.assertEqual(subscriber.namespace, 'member')
        # construct with kwargs, but no email or id, expect error:
        self.assertRaises(Invalid, ItemSubscriber, name=u'Jane Doe')
        # construct with a name as string, unicode, both save as unicode:
        subscriber = ItemSubscriber(user='jane.doe', name='Jane Doe')
        self.assertEqual(subscriber.name, u'Jane Doe', 'name not unicode')
        subscriber = ItemSubscriber(user='jane.doe', name=u'Jane Doe')
        self.assertEqual(subscriber.name, u'Jane Doe', 'name not unicode')
        # try constructing with name, email, user, default namespace
        subscriber = ItemSubscriber(
            name=u'Jane Doe', email='jdoe@example.com', user='jane.doe',)
        self.assertEqual(subscriber.name, u'Jane Doe')
        self.assertEqual(subscriber.user, 'jane.doe')
        self.assertEqual(subscriber.email, 'jdoe@example.com')
        self.assertEqual(subscriber.namespace, 'member') #default namespace
        # try constructing with all fields, test namespace:
        subscriber = ItemSubscriber(
            name=u'Jane Doe',
            email='jdoe@example.com',
            user='jane.doe',
            namespace='some_directory')
        self.fail_on_err(ValidationError,
            getSchemaValidationErrors,
            IItemSubscriber,
            subscriber)
        self.assertEqual(subscriber.namespace, 'some_directory')
        # keyword arguments should normalize unicode <--> string for all fields
        subscriber = ItemSubscriber(
            name='Jane Doe',                #stored as unicode, passed as str
            email=u'jdoe@example.com',      #stored as str, passed as unicode
            user=u'jane.doe',               #stored as str, passed as unicode
            namespace=u'some_directory')    #stored as str, passed as unicode
        self.fail_on_err(ValidationError,
            getSchemaValidationErrors,
            IItemSubscriber,
            subscriber)


class ContainerTest(unittest.TestCase):
    """Test subscriber container/mapping without a ZODB fixture"""
    
    def setUp(self):
        self.container = SubscribersContainer()
        assert len(self.container) == 0
    
    def test_iface(self):
        assert ISubscribers.providedBy(self.container)
        for name in ('add','get','__getitem__','__contains__',
                     '__delitem__','__len__'):
            assert isinstance(getattr(self.container, name, None), methodtype)
    
    def test_add_remove(self):
        key = ('email', 'me@example.com')
        assert len(self.container) == 0
        assert key not in self.container
        subscriber = ItemSubscriber(name=u'Me', email='me@example.com')
        k,v = self.container.add(subscriber)
        assert k == key
        assert len(self.container) == 1
        
        # now check the key we expected to be generated in the add() operation
        assert key in self.container
        assert key in self.container.keys()
        assert subscriber in self.container.values()
        
        # subtle but important: we can identify an object as being "in" a 
        # container, but not in its keys.
        # container.__contains__ is not same as container.keys().__contains__
        assert (subscriber in self.container and 
                subscriber not in self.container.keys())
        
        # now delete using the key we expected was generated
        del(self.container[key])
        assert len(self.container) == 0
        assert key not in self.container
        
        # now try adding again, then delete using subscriber object as a key
        k,v = self.container.add(subscriber)
        assert len(self.container) == 1
        del(self.container[subscriber]) #delete using unique value
        assert len(self.container) == 0
    
    def test_add_duplicate(self):
        key = ('email', 'me@example.com')
        assert key not in self.container
        subscriber = ItemSubscriber(name=u'Me', email='me@example.com')
        k,v = self.container.add(subscriber)
        assert k == key
        assert subscriber in self.container
        assert key in self.container
        subscriber2 = ItemSubscriber(name=u'Different name, same email',
                                     email='me@example.com')
        # will not add, raises error
        self.assertRaises(ValueError, self.container.add, subscriber2)
        assert len(self.container) == 1 #size consistent
        # justify why: the key will be compositionally identical
        keyfn = self.container._normalize_key
        assert key == k == keyfn(subscriber) == keyfn(subscriber2)
    
    def test_add_subscriber_copy(self):
        mock = MockSub()
        assert IItemSubscriber.providedBy(mock)
        key = ('member', 'somebody')
        assert key not in self.container
        self.container.add(mock)
        assert key in self.container
        stored = self.container[key]
        assert IItemSubscriber.providedBy(stored)
        assert stored is not mock
        assert stored.__class__ is not mock.__class__
        assert isinstance(stored, persistent.Persistent)
        assert isinstance(stored, ItemSubscriber)
        for fieldname in ('user','namespace','email','name'):
            assert getattr(stored, fieldname) == getattr(mock, fieldname)
    
    def test_add_subscriber_ref(self):
        """Test add persistent subscriber, make reference"""
        sub = ItemSubscriber(**DATA)
        self.container.add(sub)
        assert DATAKEY in self.container
        stored = self.container[DATAKEY]
        assert stored is sub #persistent same item
        assert sub in self.container
    
    def test_add_dict(self):
        self.container.add(DATA)
        assert DATAKEY in self.container
    
    def test_add_kwargs(self):
        self.container.add(**DATA) #as kwargs, not positional dict
        assert DATAKEY in self.container
    
    def test_add_subscriber_email_only(self):
        # add by email, declare explicit namespace
        key = ('email', 'me@example.com')
        self.container.add(namespace=key[0], email=key[1])
        assert key in self.container
        sub = self.container[key]
        assert IItemSubscriber.providedBy(sub)
        IItemSubscriber.validateInvariants(sub)
        assert sub.email == key[1]
        assert sub.namespace == key[0]
        
        # add by email, should imply namespace
        self.container.add(email='gopher@example.com')
        assert ('email', 'gopher@example.com') in self.container
    
    def test_normalize_key_email(self):
        expected = ('email', 'metoo@example.com')
        sub = ItemSubscriber()
        sub.email = expected[1]
        assert self.container._normalize_key(sub) == expected
        k, v = self.container.add(sub)
        assert k == expected
        assert expected in self.container
    
    def test_normalize_key_invalid(self):
        key = 'somestring'
        self.assertRaises(KeyError, self.container.add, key)
        badsub = ItemSubscriber()
        badsub.email = None
        badsub.user = None
        self.assertRaises(Invalid, self.container.add, badsub)
    
    def test_contains(self):
        mock = MockSub()
        self.container.add(mock)
        assert mock not in self.container # merely a copy of mock was added
        assert self.container._normalize_key(mock) in self.container
        del(self.container[mock])
        assert self.container._normalize_key(mock) not in self.container
    
    def test_len(self):
        assert hasattr(self.container, 'size')
        self.assertEqual(self.container.size(), 0)
        self.assertEqual(self.container.size(), len(self.container))
        k,v = self.container.add(email='me@example.com')
        self.assertEqual(self.container.size(), 1)
        self.assertEqual(self.container.size(), len(self.container))
        del(self.container[k])
        self.assertEqual(self.container.size(), 0)
        self.assertEqual(self.container.size(), len(self.container))
        self.container.add(email='you@example.com')
        self.assertEqual(self.container.size(), 1)
        self.assertEqual(self.container.size(), len(self.container))
        k,v = self.container.add(email='me@example.com')
        self.assertEqual(self.container.size(), 2)
        self.assertEqual(self.container.size(), len(self.container))
        del(self.container[k])
        self.assertEqual(self.container.size(), 1)
        self.assertEqual(self.container.size(), len(self.container))
    
    def tearDown(self):
        for key in list(self.container):
            del(self.container[key])
        self.assertEquals(len(self.container), 0)


if __name__ == '__main__':
    unittest.main()


