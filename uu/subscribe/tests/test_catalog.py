import uuid
import unittest2 as unittest

from zope.schema import ValidationError

from uu.subscribe.interfaces import IItemSubscriber, ISubscriptionIndex
from uu.subscribe.subscriber import ItemSubscriber
from uu.subscribe.catalog import SubscriptionCatalog
from uu.subscribe.index import SubscriptionIndex
from uu.subscribe.tests.common import DATA, DATAKEY, MockSub


# some basic common fixtures for this catalog test
UID1 = str(uuid.uuid4())
UID2 = str(uuid.uuid4())
SUB1 = MockSub()
SUB1.user = 'Ford'
SUB2 = MockSub()
SUB2.user = 'Toyota'


class CatalogTest(unittest.TestCase):
    """Test catalog of uids to subscriber signatures"""
    
    def setUp(self):
        self.catalog = SubscriptionCatalog()
    
    def test_index(self):
        assert len(self.catalog.indexes) == 0
        self.catalog.index(SUB1, UID1, 'like')
        assert len(self.catalog.indexes) == 1
        assert 'like' in self.catalog.indexes
        idx = self.catalog.indexes['like']
        assert UID1 in idx.item_uids_for(SUB1)
        assert SUB1.signature() in idx.subscribers_for(UID1)
        self.catalog.index(SUB2, UID1, ('like', 'love'))
        assert UID1 in idx.item_uids_for(SUB2)
        idx2 = self.catalog.indexes['love']
        assert UID1 in idx2.item_uids_for(SUB2)
        assert SUB2.signature() in idx2.subscribers_for(UID1)
        assert UID1 not in idx2.item_uids_for(SUB1) #SUB1 likes, not loves
        assert SUB1.signature() not in idx2.subscribers_for(UID1)
        return self.catalog #for (explicit only) re-use by other tests
    
    def test_unindex(self):
        self.catalog = self.test_index()
        self.catalog.unindex(SUB2, UID1, 'love') #sub2 likes, no longer loves
        idx_love = self.catalog.indexes['love']
        idx_like = self.catalog.indexes['like']
        assert UID1 not in idx_love.item_uids_for(SUB2)
        assert SUB2.signature() not in idx_love.subscribers_for(UID1)
        assert UID1 in idx_like.item_uids_for(SUB2)
        assert SUB2.signature() in idx_like.subscribers_for(UID1)
    
    def test_search_items(self):
        self.catalog = self.test_index()
        r = self.catalog.search({'like': SUB1}) #search for items SUB1 likes
        assert UID1 in r
        r = self.catalog.search({'love': SUB1}) #search for items SUB1 likes
        assert len(r) == 0
        r = self.catalog.search({'love': SUB2}) #search for items SUB1 likes
        assert UID1 in r
    
    def test_search_subscribers(self):
        self.catalog = self.test_index()
        r = self.catalog.search({'love': UID1}) #search for subs that like UID1
        assert SUB2.signature() in r
        assert SUB1.signature() not in r
        r = self.catalog.search({'like': UID1})
        assert SUB2.signature() in r
        assert SUB1.signature() in r
        # now, test intersection
        r = self.catalog.search({'like': UID1, 'love': UID1})
        assert SUB2.signature() in r
        assert SUB1.signature() not in r
        # empty intersection, no results:
        self.catalog.indexes['hate'] = SubscriptionIndex('hate') #empty
        r = self.catalog.search({'like': UID1, 'hate': UID1})
        assert len(r) == 0


if __name__ == '__main__':
    unittest.main()
