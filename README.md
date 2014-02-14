Phone-Based Interface Descriptions
==================================

These scripts show an example of the following:

    1. How to interact with the HTTPS interface on Cisco switches.
    2. How to interact with the AXL/SOAP/XML API on Cisco Unified Communications Manager.

The only external module required is [requests](http://docs.python-requests.org/en/latest/).
cdp\_cucm.py

This script queries a Cisco switch for its CDP neighbor table and extracts
the device names of the attached IP phones.

It then uses the companion module cucm\_query.py to query the CUCM database
via its XML SOAP API for the descriptions of those phones.

Finally, it either:

    a) interactively prints an interface configuration for the switch that 
       uses the description field as an interface description (suitable for
       copy and paste), or
    b) configures the switch with those interface descriptions via the switch
       HTTPS interface.

Thus, if a phone's description in the CUCM database is "Alice's Phone", the
new interface configuration would be:

    interface {type/number}
      description Alice's Phone

You need to set up your switch to allow configuration via the HTTPS interface,
through whatever authentication mechanism your switch uses (TACACS+, etc.).

This has been tested only on reasonably recent versions of IOS for 
Catalyst 3560/3750 switches and CUCM 8.6.
