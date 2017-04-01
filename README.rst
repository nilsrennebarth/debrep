======
debrep
======
A tool to create and maintain signed debian package repositories.

The software is currently in a pre-alpha stage. Adding (binary) packages
works, with all options mentioned in the manpage.
Files are generated/updated and Release files updated and signed.
Listing packages works as well.

Deletion, moving and source packages are not supported yet,
Very few checks, in particular for the configuration are done.


Features
========

Installation
============
Put the ``dr_lib`` directory in your standard python search path,
and debrep somewhere in your path. Create a directory
to hold your repository, and a subdir ``db`` where debrep
will create the sqlite database.

Configuration
=============

See design.rst, section Configuration items for now. You will need a
config file, either in a global or in a user-specific location or
relateive to the current working directory. The minimum
config file is::

  releases:
  - name: foorel




Usage
=====
See the manpage.

Use::

  debrep add [-R release -C component ] file ...

to add packages to the repository.






