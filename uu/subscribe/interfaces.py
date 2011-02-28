from zope.interface import Interface
from zope.interface import invariant, Invalid
from zope.interface.common.mapping import IFullMapping
from zope import schema


# core entity interface:

class IItemSubscriber(Interface):
    """
    Principal, party, or person potentially associated with a content item.
    
    While neither user nor email is required on their own, one or the other
    should be provided.
    """
    user = schema.BytesLine(
        title=u'User ID',
        description=u'System user id, may be member id or generated token',
        required=False)
    namespace = schema.BytesLine(title=u'User ID namespace', default='member')
    email = schema.BytesLine(title=u'Email address', required=False)
    name = schema.TextLine(title=u'Full name', required=False)
    
    @invariant
    def user_or_email_provided(obj):
        """
        Either or both user and/or email must be provided: necessary to
        resolve and identify the principal in meaningful ways.
        """
        if not (obj.email or obj.user):
            raise Invalid('Neither email nor user id provided for user.')


# adapter interfaces for some context:

class ISubscribersOf(Interface):
    """
    Provides query adapter to get IItemSubscriber objects given the context
    of an item.  find() resolves an iterable of IItemSubscriber objects
    given any known relationship name.
    """
    
    def find(name):
        """
        Return iterable of IItemSubsribers who match relationship name,
        may return empty iterable on no match.
        
        If (relationship) name is unknown to the system, may raise a
        ValueError complaining about such.
        """


class IItemsFor(Interface):
    """
    Provides query adapter to get item objects given the context of an
    IItemSubscriber object.  find() resolves an iterable of item objects
    for the subscriber context if relationship name is resolvable.
    
    Note: find() iterates providing item objects, not merely [U]UIDs, even if
    the storage and/or indexing implementation uses UIDs (or other
    identifiers), allowing for lazy object resolution.
    """
    
    def find(name):
        """
        Return iterable of item object references given a relationship name
        for all items related to the subscriber context by that name.  May
        return empty iterable on no match.
        
        If (relationship) name is unknown to the system, may raise a
        ValueError complaining about such.
        """


class ISubscriptionIndexer(Interface):
    """
    Adapts an item context, responsible for associating a subscriber to the
    item, or disassociating them, given a relationship name.
    
    Relationship names can be passed as string / unicode, but should be
    normalized as UTF-8 formatted strings if passed as unicode.
    """
    
    def associate(subscriber, rel):
        """
        Given a subscriber providing IItemSubscriber and a string/unicode
        name of a relationship, bind the subscriber to the item in the context
        of that relationship.
        """
    
    def disassociate(subscriber, rel):
        """
        Given a subscriber providing IItemSubscriber or a string identifier
        of user id or email, disassociate as needed for relationship named by
        rel, passed as a string or unicode.
        """


# utility and index interfaces:

class ISubscriptionIndex(Interface):
    """
    Each index is named, and is assumed to be accessed either via a 
    containing catalog or (with component lookup) as a named utility.
    
    Two-way index (forward/reverse) associating subscribers with item [U]UIDs.
    
    Forward index:
     * Keys are strings: unique ids of item objects (UID or UUID).
     * Values are objects providing IItemSubscriber.
     * Accessed via subscribers_for(item_uid)
    
    Reverse indexes:
     * Keys are strings, id or email associated with an IItemSubscriber.
       * Query function item_uids_for() can accept an IItemSubscriber object
         as well as user id/email.
     * Values are string unique ids of item objects (e.g. UID or UUID).
     * Access via item_uids_for(subscriber)
    
    Limitations of scope:
    
      * Mapping implementation is not implied here (e.g. OOBTree, dict, etc).
        
      * Indexes are not responsible for resolving objects, but UIDs; 
        other tools or utilities may be needed to resolve object references
        from the UIDs provided.

    Note about relationship names: they should be chosen such that:
      (1) a subscriber is considered the subject;
      (2) the relationship name is a word or phrase predicate;
      (3) the item is considered the object of the predicate.
    """

    name = schema.BytesLine(
        title=u'Relationship name',
        description=u'The relationship identifier for the subscription.',
        default='subscriber')
    
    def index(subscriber, item_uid):
        """
        Given an subscriber and and item_uid, associate for this index in
        both (subscriber to items) and (item to subscribers) mappings.
        """
    
    def unindex(subscriber, item_uid):
        """
        Given an subscriber and item_uid, remove any associations in this
        index between them.
        """
    
    def item_uids_for(subscriber):
        """
        Given subscriber as EITHER an object providing IItemSubscriber OR as
        string id/email of subscriber, find and return tuple of item UIDs.
        """
    
    def subscribers_for(item_uid):
        """
        Given an item UID, find and return a tuple of objects providing
        IItemSubscriber for that item UID.
        """


class ISubscriptionCatalog(Interface):
    """
    Container for all subscription indexes.
    """
    
    indexes = schema.Object(
        title=u'Contained indexes',
        description=u'Relationship name keys map to contained Index values '\
                    u'providing ISubscriptionIndex. ',
        schema=IFullMapping)
    
    metadata = schema.Object(
        title=u'Association metadata',
        description=u'Metadata or information associated with a '\
                    u'relationship, keyed off of the unique triple of '\
                    u'(subscriber_id, item_id, relationship name) as '\
                    u'subject/object/predicate.  Values are mappings '\
                    u'of schemaless name/value pairs.',
        schema=IFullMapping,
        )
    
    subscribers = schema.Object(
        title=u'Registered subscribers',
        description=u'All subscriber objects managed by this catalog',
        schema=IFullMapping,)
    
    items = schema.Object(
        title=u'Registered item uids',
        description=u'All items managed, referenced by this catalog',
        schema=IFullMapping,)
    
    def search(**kwargs):
        """
        Given keyword arguments, where keys are index/relationship names,
        and values are either IItemSubscriber objects, or item UIDs, return
        an iterable of intersecting resulting item UIDs or IItemSubscriber
        objects, respectively such that all UIDs or subscribers returned
        match all criteria.
        
        Search criteria/arguments for names of indexes not managed by this
        catalog should be ignored silently.
        """

