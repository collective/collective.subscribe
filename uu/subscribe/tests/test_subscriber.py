
import sys
import unittest2 as unittest

from zope.interface import Invalid
from zope.schema import getSchemaValidationErrors, ValidationError

from uu.subscribe.interfaces import IItemSubscriber
from uu.subscribe.subscriber import ItemSubscriber


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


if __name__ == '__main__':
    unittest.main()


