collective.subscribe 
====================

Usage
=====

This package deals with relationships between subscribers and content items.

A subscriber is an entity that contains some identifying metadata fields:

    >>> from collective.subscribe.interfaces import IItemSubscriber
    >>> from collective.subscribe.subscriber import ItemSubscriber
    >>> subscriber = ItemSubscriber()
    >>> assert IItemSubscriber.providedBy(subscriber)
    >>> from zope.schema import getFieldsInOrder
    >>> for name, field in getFieldsInOrder(IItemSubscriber):
    ...     print name, type(field)
    ... 
    user <class 'zope.schema._field.BytesLine'>
    namespace <class 'zope.schema._field.BytesLine'>
    email <class 'zope.schema._field.BytesLine'>
    name <class 'zope.schema._bootstrapfields.TextLine'>


Each subscriber has a distinct signature acting as a compositional identity,
based upon either a user name or an email address, prefaced with an
identity namespace.  The default namespace for a subscriber is member, useful
for users within an application/site:

    >>> subscriber.namespace
    'member'


Attempting to obtain a signature on a subscriber empty of either id or email
yeilds an exception:

    >>> subscriber.signature() #DOCTEST:ellipsis
    Traceback (most recent call last):
    ...
    Invalid: Neither email nor user id provided for user.


However, setting the user property or the email property makes it possible
to obtain a signature:

    >>> subscriber.user = 'someone'
    >>> subscriber.signature()
    ('member', 'someone')


When email is used, and the user field is None, the signature ignores the
namespace field, and returns a namespace of email:

    >>> subscriber.user = None
    >>> subscriber.email = 'me@example.com'
    >>> subscriber.namespace
    'member'
    >>> subscriber.signature()
    ('email', 'me@example.com')
    >>> assert subscriber.signature()[0] != subscriber.namespace

However, the above behavior is a special case for when user is None.  If 
both user and email (or just user) is set, the namespace set on the 
subscriber is always considered:

    >>> subscriber.user = 'me'
    >>> subscriber.namespace
    'member'
    >>> subscriber.signature()
    ('member', 'me')
    >>> assert subscriber.signature()[0] != 'email'
    >>> subscriber.user = None
    >>> subscriber.signature()
    ('email', 'me@example.com')


Subscribers can be stored in a container, which is a mapping in which keys
are signatures, and values are objects providing IItemSubscriber.  A few
things are worth note:

 * Containment, get, delete operations should be able to key an item by
   an object, by looking up its signature.

 * Containers and items contained may or may not be persistent, depending
   upon application; the implementations here are ZODB-enabled, but not
   required to be persistently stored.

Create a container:

    >>> from collective.subscribe.interfaces import ISubscribers
    >>> from collective.subscribe.subscriber import SubscribersContainer
    >>> container = SubscribersContainer()
    >>> assert ISubscribers.providedBy(container)

Containers act like mappings:

    >>> assert len(container) == 0
    >>> assert len(container.keys()) == 0
    >>> assert hasattr(container, '__setitem__')
    >>> assert container.get(('member', 'nonexist'), None) is None

But containers also have a distinct add() operation:

    >>> signature, sub = container.add(subscriber)
    >>> assert sub is subscriber

Checking for containment can be done by object or by signature:

    >>> assert subscriber in container
    >>> assert subscriber.signature() in container
    >>> assert container.get(subscriber.signature(), None) is subscriber
    >>> assert container.get(subscriber) is subscriber
    >>> assert subscriber.signature() in container.keys()
    >>> assert subscriber not in container.keys() # an important subtlety

Whether a container stored by reference or by copy on add depends on the
compatibility of the implementation of the object providing IItemSubscriber.
For example, this mock subscriber object is not known to the container, so
it keeps a copy:

    >>> from collective.subscribe.tests.common import MockSub
    >>> subscriber2 = MockSub()
    >>> assert IItemSubscriber.providedBy(subscriber2)
    >>> signature, sub = container.add(subscriber2)
    >>> assert sub is not subscriber2
    >>> assert sub.signature() == subscriber2.signature()
    >>> assert subscriber2.signature() in container
    >>> assert subscriber2 not in container.values() #no, a copy of sub is!
    >>> assert sub in container.values() # this is the actual stored object
    >>> assert subscriber2.signature() in container.keys()
    >>> assert container.get(signature) is sub
    >>> assert container.get(signature) is not subscriber2


A subscriber is only interesting insofar as it can be related by association
name to one or more content items.  The purpose of subscription is to 
express the subscriber's relationship to the content item (and vice versa).
In order to use subscription information, we need to be able to query it
from indexes. For this purpose, collective.subscribe provides a purpose-specific
catalog in which each index represents a named relationship such as 'like',
'subscribe', 'invited', 'confirmed', etc.

Let's get a catalog:

    >>> from collective.subscribe.interfaces import ISubscriptionCatalog
    >>> from collective.subscribe.catalog import SubscriptionCatalog
    >>> catalog = SubscriptionCatalog()
    >>> assert ISubscriptionCatalog.providedBy(catalog)

A catalog has a mapping of indexes and a mapping of metadata as part of its
public interface:

    >>> assert hasattr(catalog, 'index')    # a PersistentDict
    >>> assert hasattr(catalog, 'metadata') # an OOBTree

Note: metadata can be arbitrary objects, but likely should be schema-less 
mapping objects containing key-value pairs of association metadata.  The
use of metadata is yet to be described in this documentation.

In order to do anything meaningful with a catalog, we need some example 
(mock) content items that each have a [U]UID:

    >>> import uuid
    >>> class MockContent(object):
    ...     def __init__(self, title='content'):
    ...         self._uid = str(uuid.uuid4())
    ...         self.title = title
    ...     def UID(self):
    ...         return self._uid
    ... 
    >>> power = MockContent('power')
    >>> reformation = MockContent('reformation')

Note: the assumption that mock content has a method called UID is for
convenience, not by mandate (in reality, adapters should be used to get
the UID of an object/item).

We also want some mock subscribers to index in the catalog:

    >>> henry = ItemSubscriber()
    >>> henry.name = u'Henry Tudor'
    >>> henry.user = 'henryVIII'
    >>> assert henry.signature() == ('member', 'henryVIII')
    >>> mary = ItemSubscriber()
    >>> mary.name = u'Mary Mary quite contrary'
    >>> mary.email = 'bloodymary@example.com'
    >>> assert mary.signature() == ('email', 'bloodymary@example.com')

Indexes for a new catalog are initially empty.  It is expected that indexes
will usually be created as needed when items are indexed.

    >>> assert len(catalog.indexes) == 0
    >>> catalog.index(henry, power.UID(), 'likes')
    >>> assert len(catalog.indexes) == 1
    >>> assert 'likes' in catalog.indexes
    >>> assert henry.signature() in catalog.search({'likes': power.UID()})
    >>> assert power.UID() in catalog.search({'likes': henry})

We can get individual index objects:

    >>> from collective.subscribe.interfaces import ISubscriptionIndex
    >>> idx = catalog.indexes['likes']
    >>> assert ISubscriptionIndex.providedBy(idx)


More examples of catalog and index usage are provided in the unit tests of
this package.

Putting it all together: component registrations
------------------------------------------------

Here is an example of using components from this package with registrations.
Note that these are not provided by this package, but should be registered
by consuming packages or applications.

First, we'll use the global site manager from zope.component as our registry:

    >>> from zope.component import getGlobalSiteManager, queryUtility
    >>> gsm = getGlobalSiteManager()

Next, we'll register utilities, and check lookup: 

    >>> gsm.registerUtility(container, ISubscribers)
    >>> gsm.registerUtility(catalog, ISubscriptionCatalog)
    >>> con = queryUtility(ISubscribers)
    >>> cat = queryUtility(ISubscriptionCatalog)
    >>> assert con is container
    >>> assert cat is catalog

We can use catalog and container in concert; let's add a cataloged
subscriber to the container (in practice, this is usually done in the
opposite sequence, but it is not of consequence):

    >>> k,v = container.add(henry)
    >>> k,v = container.add(mary)

Now that we have registered the subscribers container as a utility, we can
use the catalog as a front to the container as well:

    >>> assert catalog.get_subscriber(mary.signature()) is mary

This is useful in a query:

    >>> result = catalog.search({'likes':power.UID()})
    >>> assert henry in [catalog.get_subscriber(sig) for sig in result]

An advantage to using this approach is that they catalog component looks up
the container once (per thread) and caches a volatile (_v_) reference to it.
For a large result set, calling code could use a generator to create an 
iterable over a result set of signatures, fetching subscribers as needed on
iteration (or alternatively use a lazy sequence).

We can create an item resolver utility and a UID adapter for our mock content:

    >>> from collective.subscribe.interfaces import IUIDStrategy, IItemResolver
    >>> from zope.interface import implements
    >>> class DumbItemResolver(object):
    ...     implements(IItemResolver)
    ...     def get(self, uid):
    ...         if uid == power.UID():
    ...             return power
    ...         if uid == reformation.UID():
    ...             return reformation
    ...         return None
    ... 
    >>> gsm.registerUtility(DumbItemResolver())
    >>> resolver = queryUtility(IItemResolver)
    >>> assert resolver.get(power.UID()) is power
    >>> assert catalog.get_item(power.UID()) is power

We can also create a UID adapter particular to a framework (in this case, 
our framework is the contract of our mock content):

    >>> from zope.interface import Interface
    >>> from zope.component import adapts
    >>> class MockContentUID(object):
    ...     implements(IUIDStrategy)
    ...     adapts(Interface) #adapts anything, in this trivial case
    ...     def __init__(self, context):
    ...         self.context = context
    ...     def getuid(self):
    ...         return self.context.UID()
    ...     __call__ = getuid
    ... 
    >>> gsm.registerAdapter(MockContentUID)
    >>> assert IUIDStrategy(reformation).getuid() == reformation.UID()

About
-----

Author: Sean Upton <sean.upton@hsc.utah.edu>

Copyright, (c) 2011 The University of Utah

Licensed under an MIT-style license, see COPYING.txt in the source of this
package.

