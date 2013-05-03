Introduction
============

collective.subscribe contains components for associating users/principals as
subsribers to an item of content, maintaining a relationship between
them, and providing an index for such relationships.

This package provides underlying components that use and integrate with
the Zope Component Architecture (ZCA), and can be used by higher-level
packages providing application-specific uses of the adapters, entities,
utilities, and indexes provided by this package.

A library for user subscription to content
==========================================

collective.subscribe is a library package of components for describing,
working with, and indexing named user-to-content relationships for
any identfiable identification schemes for either users or for content
unique ids.

This package provides utilities and adapters for establishing and querying
relationships between users "subscribing to" content in some meaningful
named relationship:

 * User "subscribes to" content
 * User "likes" (or "dislikes" content
 * User "is invited to" (event or meeting) content
 * User "attended" (event or meeting) content

This package depends upon the Zope Component Architecture and the ZODB
as upstream dependencies, but could be used in any Python application 
where the core interfaces (IItemSubscriber, adapter and index interfaces)
are useful.  

The designed purpose of this application is to support a generic set of 
relationships for higher-level packages.  For example, an add-on for 
Plone providing a local utility extrinsically indexing subscription 
relationships could be useful to describe user (member, non-member) 
invitations, confirmations, and attendance of event (as meeting) content.


Integration note
----------------

This package is intended for use as a framework component for other packages
and libraries, and does not register any components.  The reasons for this:

 * We should not presume callers will use a global site manager.
 
 * We should not presume that all uses will be persistent local utilities;
   while ZODB is a requirement for this package, and all components here
   are subclassing persistent, they can be used in a purely transient 
   capacity in a non-ZODB application.

 * It is conceivable that subclasses, adapters, or re-implementations of 
   components (re-using interfaces) is possible for alternate storage
   implementations in adjacent packages (for example, storing in RDF 
   or a relational database using ORM).

 * For Plone apps, we want persistent local utilities to be set up at the 
   discretion of Plone-specific calling packages. The same is true for other
   Zope-based applications and frameworks (e.g. Grok, BlueBream, Sliva, etc).

 * Below in usage documentation are examples of component registration, 
   which use the global site manager.  Actual usage may vary, but the
   usage below provides an example integration for documentation (and
   testing) purposes.


Identifying subscribers
-----------------------

What is compositional identity?  Our assumption is that a unique identity of
a subscriber is composed of a namespace, followed by a string identifying 
the user uniquely within the context of that namespace.

Examples:

 * ('uuid', '68c47dd7-897d-43f1-b610-a6a8c885fe36')

 * ('member', 'johndoe')

 * ('email', 'jdoe@example.com')

 * ('openid', 'https://me.yahoo.com/seanupton')

Why use compositional identity, versus alternatives?

 * Compared to UUID: composition is human readable, also supports a
   pairing that can easily be universally unique.  Compositional ids are
   easier to generate deterministically than an RFC 4122 UUID version 3
   identifier, and easier to code for.  However, it is possible to use a
   UUID as *part of* a composional identity (see example above).

 * Compared to integer ID: less likelihood of collision.  As long as
   namespaces are system-unique, an integer ID of a subscriber could
   well be *part of* a compositional identity, albeit in string form.

What is a signature?

 * A signature is a generated composed key (compositional identity) for a
   subscriber object based upon its metadata, and is guaranteed to be 
   deterministic (can be re-generated from object) and reasonable for
   use as a unique key describing a party.  The IItemSubscriber interface
   prescribes a signature() method for subscriber objects, provided 
   sufficient metadata (either email or username).


People
======

* Sean Upton <sean.upton@hsc.utah.edu> (author)
* Thomas Desvenain <thomas.desvenain@gmail.com>

This package is released under an MIT license; see docs/COPYING.txt
Copyright (c) 2011, The University of Utah

