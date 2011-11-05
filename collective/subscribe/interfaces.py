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
    
    def signature():
        """
        return a composed key signature tuple of (namespace, user or email).
        The special namespace 'email' will be used for subscriber objects
        with no user field value, but containing an email value. If user 
        field value is present, it will be preferred to email, unless the 
        namespace is explicitly set to 'email'.
        
            * Both namespace and user id must be strings.
            
            * Valid example values:
            
                ('uuid', '68c47dd7-897d-43f1-b610-a6a8c885fe36')
                ('member', 'johndoe')
                ('email', 'jdoe@example.com')
                ('openid', 'https://me.yahoo.com/seanupton')

            * Raises a zope.interface.Invalid exception if signature is not
                possible due to insufficient field data.
        """
    
    @invariant
    def user_or_email_provided(obj):
        """
        Either or both user and/or email must be provided: necessary to
        resolve and identify the principal in meaningful ways.
        """
        if not (obj.email or obj.user):
            raise Invalid('Neither email nor user id provided for user.')


# container interface for persisting subscribers:

class ISubscribers(Interface):
    """
    Container for subscribers; mapping is keyed off of a unique identifier
    for a subscriber, either (but not both):
    
      (1) a tuple of (namespace, user id) [preferable if available].
            
            * Both namespace and user id must be strings.
            
            * Valid example values:
            
                ('uuid', '68c47dd7-897d-43f1-b610-a6a8c885fe36')
                ('member', 'johndoe')
                ('email', 'jdoe@example.com')
                ('openid', 'https://me.yahoo.com/seanupton')
    
      (2) an email address.
    
    Note:   one record keyed off email and another record storing
            the same email keyed off another schema are considered
            distinct and *un-related*.
    
    Mapping/contained values MUST be objects implementing IItemSubscriber.

    This interface is a partial mapping interface; for example, it does not
    mandate nor guarantee that __setitem__() will be available (it is not
    preferred; use of add() and __delitem__() are recommended instead, as
    add() handles key generation from an object providing IItemSubscriber).
    
    Compositional identity: keys are composed as composite keys based on
    field attributes/properties of each IItemSubscriber object value. 
    This means that operations like containment, get, removal can use 
    keys and values interchanably, and that add can deterministically 
    generate a key based upon the subscriber object.
    """
    
    def add(*args, **kwargs):
        """
        Add (and optionally construct and add) a subscriber object to the
        this container of subscribers.
        
        The first positinal argument can be either an object providing the
        IItemSubscriber interface or a dict of field values to construct
        such an object (in such case, key names match field names in the
        IItemSubscriber schema).
        
        Alternately, if positional arguments are omitted and keyword arguments
        are provided, such that the keyword arguments are sufficient to 
        construct an item subscriber.
        
        Returns a tuple of (generated key, subscriber object).

        This method always returns a reference to a distinct subscriber
        object within the tuple return value, such that the subscriber
        object can be updated, and that updates are reflected in stored
        (transient or persisted) values within this container. 
        
        Implementations should validate IItemSubscriber invariants on
        objects to be added.
        
        When passed an object providing IItemSubscriber, it is to be 
        considered implementation-specific and outside of interface scope
        whether this operation stores a reference to that object or 
        merely copies its values into a new object also providing
        IItemSubscriber.  On the other hand, if this operation constructs
        such an object, there is less confusion.
        
        If an existing record exists for the generated item, raise a
        ValueError (callers should verify first if item exists via 
        __contains__(key) or __contains__(subscriber) checks).

        On an invalid key passed to add, raise a KeyError.
        """
    
    def get(key, default=None):
        """
        Given a subscriber key as either tuple of (namespace, userid) or
        as string email address, return record or default.
        """
    
    def __getitem__(key):
        """
        Given a subscriber key as either tuple of (namespace, userid) or
        as string email address, return record or raise KeyError.
        """
    
    def __len__():
        """Return length of container (number of records)."""
    
    def __contains__(key):
        """
        Return True if subscriber key in container keys; otherwise False.
        May also be passed key as an object providing IItemSubscriber, in
        which case, such object is used to make a key to check for
        containment.
        
        If containment is checks on an object providing IItemSubscriber, it
        will only return true if the object passed is identical to the object
        stored.
        """
    
    def __delitem__(key):
        """
        Delete subscriber from container given subscriber as any of:
            
            (1) object providing IItemSubscriber; needs not be
                identical to object actually stored, used as a
                template to generate a key for deletion.
            
            (2) dict providing a template used for generation of a
                unique key for deletion.
            
            (3) a key as (namespace, user) tuple or string email address.
        
        Raises KeyError if key is not found.
        """


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
    
    def subscriptions_for(subscriber):
        """
        Given subscriber as object providing IItemSubscriber or as
        a subscriber signature tuple, return all known relationship
        names (list of strings) for which the subscriber is subscribed
        to the item for the context adapted.
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


# utility and index interfaces:

class ISubscriptionIndex(Interface):
    """
    Each index is named, and is assumed to be accessed either via a 
    containing catalog (keyed by name) or component lookup of a named utility.
    
    Two-way index (forward/reverse) associating subscribers with item [U]UIDs.
    
    Forward index:
     * Keys are strings: unique ids of item objects (UID or UUID).
     * Values are tuple composed keys suitable for ISubscribers containers,
        in the format (namespace, user_or_email) where both contents of the
        tuple key are strings.
     * Accessed via subscribers_for(item_uid)
    
    Reverse indexes:
     * Keys are tuple composed keys suitable for ISubscribers containers,
        in the format (namespace, user_or_email) where both contents of the
        tuple key are strings.
     * Values are string unique ids of item objects (e.g. UID or UUID).
     * Access via item_uids_for(subscriber)
    
    Limitations of scope:
    
      * Mapping implementation is not implied here (e.g. OOBTree, dict, etc).
        
      * Indexes are not responsible for resolving item of subscriber 
        objects, but UIDs of item objects and composed keys for subscribers; 
        other tools or utilities may be needed to resolve object references
        from the UIDs and keys provided.

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

        The subscriber argument can be either a two-item tuple key or
        an IItemSubsriber object, in which case the key will be extracted
        by calling the signature() method of the subscriber.
        """
    
    def unindex(subscriber, item_uid):
        """
        Given an subscriber and item_uid, remove any associations in this
        index between them.
        
        The subscriber argument can be either a two-item tuple key or
        an IItemSubsriber object, in which case the key will be extracted
        by calling the signature() method of the subscriber.
        """
    
    def item_uids_for(subscriber):
        """
        Find, return tuple of item UIDs given a subscriber for this index.
        
        The subscriber argument can be either a two-item tuple key or
        an IItemSubsriber object, in which case the key will be extracted
        by calling the signature() method of the subscriber.        
        """
    
    def subscribers_for(item_uid):
        """
        Given an item UID, find and return a tuple of subscriber signatures
        (composed keys) for subscribers an item in this index.
        """


class ISubscriptionCatalog(Interface):
    """
    Container for all subscription indexes.
    
    Note: subscribers MUST be identified by 64-bit integers in indexes
    which can be resolved to persisted subscriber records stored as values
    in the mapping self.subscribers.
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
                    u'(subscriber key, item uid, relationship/index name) '\
                    u'as subject/object/predicate.  Values are mappings '\
                    u'of schemaless name/value pairs.',
        schema=IFullMapping,
        )
        
    def search(query):
        """
        Searches one or more indexes specified in query for relationships
        between subscribers and items.  What is returned in the result
        sequence (signatures or item uids) depends on the query passed.
        
        Unnamed query (all subscriptions)
        ---------------------------------

        If query is not a dict/mapping, then it may be of the following:

            (1) IItemSubscriber object

                Return sequence of all content items related in any 
                way (any relationship name known) for subscriber.

            (2) Two-item subscriber signature tuple.

                Also returns item sequence for all items related.

            (3) A UID string.

                Returns a sequence of subscriber signature tuples of all
                subscribers related (any relationship name) for item.

        Named Subscriptions
        -------------------

        Given query as dict/mapping, where keys are index/relationship
        names, and values are any of:
            
            (1) IItemSubscriber object
            
                * Search for item UIDs.
            
            (2) A two-item string tuple acting as a subscriber key/signature.
            
                * Search for item UIDs.
            
            (3) An single string, assumed to be an item UID.
            
                * Search for subscribers, return signature tuples of 
                  subscriber namespace and identifier.
        
        Search criteria/arguments for names of indexes not managed by this
        catalog should be ignored silently.
        """
    
    def index(subscriber, uid, names):
        """
        Index a set of named relationships enumerated in names -- this
        argument may EITHER be a single string or a sequence of string 
        names of relationships -- for item uid, subscriber to respective
        indexes.  If an index for a name does not yet exist, this 
        operation will create and manage such an index.
        
        The subscriber argument can be either a two-item tuple key or
        an IItemSubsriber object, in which case the key will be extracted
        by calling the signature() method of the subscriber.
        """
    
    def unindex(subscriber, uid, names):
        """
        Remove named relationships, and remove any association metadata
        for each name in names for the given item uid and subscriber.  
        
        The subscriber argument can be either a two-item tuple key or
        an IItemSubsriber object, in which case the key will be extracted
        by calling the signature() method of the subscriber.
        
        Note: empty indexes are not removed or pruned from self.indexes
        by this operation, as it is of little or no cost to leave them
        around after creation, even if automatically created by index().
        """
    
    def get_item(uid):
        """
        Method should attempt to get item, possibly delegating to framework
        specific plugins (as registered utillities) to revolve UIDs to
        actual item objects.  Return None if item is not found.
        """
    
    def get_subscriber(signature):
        """
        Given a signature for a subscriber, get subscriber from
        ISubscribers utility; may cache utility lookup.  Return None if
        subscriber is not found.
        """

# configuration interfaces for UID lookup

class IUIDStrategy(Interface):
    """
    Base strategy interface for getting a UID based on object introspection.
    
    Likely used as adapter component.
    """
    
    def getuid():
        """return UID for context based upon a strategy, or None"""
    
    def __call__():
        """
        calling alias to getuid().
        """


class IItemResolver(Interface):
    """
    Item resolver interface, has get() function that takes UID, and performs
    a traversal, lookup, or load of an item object to be returned.

    Likely used as utility component.
    """
    
    def get(uid):
        """return resolved object for uid or None if not found"""


class ISubscriptionKeys(IFullMapping):
    """
    Utility component acts as many-to-one mapping of string keys to
    subscriptions expressed as three-item tuples containing in order:
    
      1. Relationship name (string).
    
      2. Subscriber signature: output of IItemSubscriber.signature()
    
      3. String [U]UID of subscribed item.
    
    Other than specifying that keys are strings, and mandating that
    components providing this interface provide a key generation 
    function -- this interface does not provide guidance on the
    algorithm or scheme of that key-generation function, which is
    implementation-specific.
    """
    
    key_description = schema.Text(
        title=u'Key description',
        description=u'Description of key generation algorithm used by '\
                    u'implementation.',
        required=False)
    
    def generate(name, signature, uid):
        """Given name, signature, uid: generate a unique string key"""
    
    def add(name, signature, uid):
        """
        Given name, signature, uid: generate key and add key/value to
        mapping; need not check for duplicate/existing, and should
        just overwrite any existing entries for key. Returns generated
        key.
        """
    
    def __setitem__(key, value):
        """
        Set item with validation of key and value; should raise
        a KeyError on a non-string key, and should raise a ValueError on
        anything that is not a tuple of (string name, subscriber signature,
        item uid string).
        """

