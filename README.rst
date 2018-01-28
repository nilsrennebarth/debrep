======
debrep
======
A tool to create and maintain signed debian package repositories.

The software is currently in the alpha stage and allows maintainting a
(binary only) debian package repository. Packages can be added, listed and
deleted. The only subcommand not yet
implemented is moving packages from one distribution to another, which is
only an optimization for deleting and adding the packages.

Still to be done:

- Source packages
- Move packages between distributions and/or components
- More validity checks in particular for the options. Currently you get
  strange and unexpected errors when options have the wrong structure or
  type.
- Different repository storage layouts:

  - Store packages in distibution and component specific paths and use
    either symlinks or hardlinks or copies for the same binary in several
    distributions.

- Various options how different versions of the same package in one
  distribution are handled:

  - Only allow one version of a package per arch/distribution, adding a
    different one automatically replaces the previous one.
  - Same as previous, but addtionally only allow strictly higher versions.
  - Allow several versions of a package per distribution

- Audit trail logging all changes to the repository.

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






