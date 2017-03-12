======
debrep
======
--------------------------------------------------------
Create and administer a signed debian package repository
--------------------------------------------------------
:Author:    Nils Rennebarth <nils.rennebarth@web.de>
:Version:   Version 0.0.1
:Copyright: 2017 by Nils Rennebarth
:License:   GNU Public License v2 (GPLv2)
:Manual section: 1

SYNOPSIS
========

*debrep* <action> [<options>] [ <arguments> ]

*debrep* *add* <package> ...

*debrep* *del* | *rm* <name> ...

*debrep* *mv* --torel <rel> --tocomp <comp> <name> ...

DESCRIPTION
===========
*debrep* is a tool to create and administer a debian package
repository. Packages can be added to or removed frome the repository. Its
content can be listed and queried.

*debrep* enters all packages added to its repository to a (sqlite) database
which is automatically created if it does not exist. The repositories it
creates are fully usable by ``apt``\(8) and use the package pool layout.

OPTIONS
=======
The usual argument conventions apply, i.e. an argument for a long option may
be separated from the option either by whitespace or an equal sign. An
argument for a short option may either follow the option directly or separated
by whitespace. Short options can be concatenated, but only the last one may
take an argument.


General options
---------------
The following options are common to all subcommands:

 --help      show usage hints
 -V, --version   show version and exit
 -v, --verbose  increase verbosity
 -s, --silent   decrease verbosity

 -C, --component <component>
   add to, remove from, list only this component. For del and ls, might
   use a comma separated list.

 -R, --release <release>
   add to, remove from, list only this release. For del and ls, might
   use a comma separated list

 -A, --architecture <architecture>
   add to, remove from, list only the given architecture(s). Several
   architectures can be given as a comma separated list

 -o, --option <optassignment>
   set a configuration option. `optassignment` has the form
   `optname` *=* `optvalue` Options given on the commandline override
   those given in the configuration file

 -c,--config <conffile>
   use the given configuration file. See ``debrep.conf``\(5) for the
   config file syntax

Add packages
------------
Packages are added with the *add* subcommand. It is followed by one or
more files that must be debian packages. Between these, assignments of the
form

  R=`release`

and

  S=`component`

can be added and will set the target release or target component respectively
for all packages that follow. Adding a package which is already present in
the archive (determined by its SHA256 checksum) will not copy the file but
simply create another reference to it. Adding a package to a release that
already contains a package of the same name will replace the previous
package.

Delete packages
---------------
Packages are removed with the *rm* or (synonymously) *del* subcommand.
It is followed by one or more package names.

List packages
-------------
The *ls* or *list* subcommand list the content of the repository.
It takes to following options:

 -f, --format <template>
  Use `template` to format the output of a single package. It can
  contain placeholders of the form *{* <name> *}* where <name> is a
  debian control file field, i.e. Maintainer, Version, ...

  In addition to standard debian control fields, the following
  can be used as well:

  Component
    the component the package is in
  Release
    the codename of the release
  Filename
    the filename relative the the repository root directory


EXAMPLES
========

:debrep add -R stable foo.deb C=contrib bar.deb:
   Add foo.deb to the default component of the stable release, and
   bar.deb to the contrib component of the stable relase

Project Homepage at https://github.com/nilsrennebarth/debrep
