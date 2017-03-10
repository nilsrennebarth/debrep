======
debrep
======
A tool to create and maintain signed debian package repositories.

The software is currently in a pre-alpha stage and not really
usable. *You have been warned*.


Features
========

Installation
============
Put the debrep directory in your standard python search path,
and debrep-add.py somewhere in your path. Create a directory
to hold your repository, and a subdir ``db`` where debrep
will create the sqlite database.

Configuration
=============

See design.rst, section Configuration items for now. You will need a
config file, either in a global or in a user-specific location or
relateive to the current working directory. The minimum
config file is::

  defrelease: foorel
  releases:
  - name: foorel




Usage
=====

Use::

  debrep-add add <foo.deb>

to add a package, and::

  debrep-add idx <relname>

to update the release file and indices.





