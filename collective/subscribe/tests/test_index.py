import uuid
import unittest2 as unittest

from zope.schema import ValidationError

from collective.subscribe.interfaces import IItemSubscriber, ISubscriptionIndex
from collective.subscribe.subscriber import ItemSubscriber
from collective.subscribe.index import SubscriptionIndex
from collective.subscribe.tests.common import DATA, DATAKEY, MockSub


class IndexTest(unittest.TestCase):
    """Test index of item uids to subscriber signatures"""

    def _set_name(self, index, name):
        index.name = name
    
    def test_name_field(self):
        index = SubscriptionIndex('related')
        assert index.name == 'related'
        self._set_name(index, 'related again')
        self.assertEqual(index.name, 'related again')
        self.assertRaises(ValidationError, self._set_name, index, u'unicode')
    
    def test_index(self):
        index = SubscriptionIndex('test_index')
        uid = str(uuid.uuid4())
        sub = MockSub()
        assert not index.item_uids_for(sub)
        assert not index.item_uids_for(sub.signature())
        assert not index.subscribers_for(uid)

        #try twice, will not duplicate index:
        for i in range(0,2):
            index.index(sub, uid)
            result_uids = index.item_uids_for(sub)
            result_subs = index.subscribers_for(uid)
            assert len(result_uids) == 1
            assert len(result_subs) == 1
            assert uid in result_uids
            assert sub.signature() in result_subs
        
        #index same intem, another sub:
        sub2 = MockSub()
        sub2.email = 'me@example.com'
        sub2.namespace = 'email'
        assert sub2.signature() == ('email', 'me@example.com')
        index.index(sub2, uid)
        result_uids = index.item_uids_for(sub2)
        result_subs = index.subscribers_for(uid)
        assert len(result_uids) == 1
        assert len(result_subs) == 2
        assert uid in result_uids
        assert sub2.signature() in result_subs
        assert sub.signature() in result_subs
        
        # return locals for continued use by other tests:
        return locals()
    
    def test_unindex(self):
        idx_locals = self.test_index()
        index = idx_locals['index']
        uid = idx_locals['uid']
        sub = MockSub()
        index.unindex(sub, uid)        
        result_uids = index.item_uids_for(sub)
        result_subs = index.subscribers_for(uid)
        assert len(result_uids) == 0
        assert len(result_subs) == 1
        assert uid not in result_uids
        assert sub.signature() not in result_subs
        sub2sig = ('email', 'me@example.com')
        assert sub2sig in result_subs #sub2 from above
        index.unindex( sub2sig, uid ) #unindex sub2
        result_uids = index.item_uids_for(sub2sig)
        result_subs = index.subscribers_for(uid)
        assert len(result_uids) == 0
        assert len(result_subs) == 0


if __name__ == '__main__':
    unittest.main()

