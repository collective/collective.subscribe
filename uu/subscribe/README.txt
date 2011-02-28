
uu.subscribe 
============

A library for user subscription to content
------------------------------------------

uu.subscribe is a library package providing components for describing,
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

Usage
-----




