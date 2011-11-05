import base64
import unittest2 as unittest
import uuid
from hashlib import md5
from new import instancemethod as methodtype

from collective.subscribe.interfaces import ISubscriptionKeys
from collective.subscribe.tests.common import MockSub
from collective.subscribe.keys import SubscriptionKeys


SUB = MockSub()
UID = str(uuid.uuid4())
NAME = 'invited'
VALID = (NAME, SUB.signature(), UID)
INVALID = ( (NAME, (), UID),
            ((), SUB.signature(), UID),
            (NAME, SUB.signature),
          )
EXPECTED = base64.urlsafe_b64encode(
    md5('%s/%s/%s' % (NAME, hash(SUB.signature()), UID)).digest())[:22]


class KeysTest(unittest.TestCase):
    """Test subscription keys mapping without a ZODB fixture"""
    
    def setUp(self):
        self.subkeys = SubscriptionKeys()
        assert len(self.subkeys) == 0
    
    def test_iface(self):
        assert ISubscriptionKeys.providedBy(self.subkeys)
        for name in ('add', 'get', '__getitem__', '__contains__',
                     '__delitem__', '__len__'):
            assert hasattr(getattr(self.subkeys, name, None), '__call__')

    def test_validation(self):
        # key must be string, not (for example) an integer
        self.assertRaises(KeyError, self.subkeys.__setitem__, 123, VALID)
        # test invalid values:
        for badvalue in INVALID:
            self.assertRaises(ValueError,
                              self.subkeys.__setitem__,
                              'abc',
                              badvalue)
        
    def test_generation(self):
        key = self.subkeys.generate(NAME, SUB.signature(), UID)
        assert key == EXPECTED
        assert key == self.subkeys.add(NAME, SUB.signature(), UID)
    
    def test_add_remove(self):
        key = self.subkeys.add(NAME, SUB.signature(), UID)
        assert key in self.subkeys
        assert key in self.subkeys.keys()
        assert self.subkeys[key] == (NAME, SUB.signature(), UID)
        del(self.subkeys[key])
        assert key not in self.subkeys
    
    def tearDown(self):
        for key in list(self.subkeys):
            del(self.subkeys[key])
        self.assertEquals(len(self.subkeys), 0)


if __name__ == '__main__':
    unittest.main()


