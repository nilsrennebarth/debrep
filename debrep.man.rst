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

 -c, --config <conffile>
   use the given configuration file. See ``debrep.conf``\(5) for the
   config file syntax

Add packages
------------
Packages are added with the *add* subcommand. It is followed by one or more
files that must be debian packages.  Adding a package which is already present
in the archive (determined by its SHA256 checksum) will not copy the file but
simply create another reference to it. Adding a package to a release that
already contains a package of the same name and architecture will replace the
previous package. In that case, the component of the package will be the new
one if they differ.

Delete packages
---------------
Packages are removed with the *rm* or (synonymously) *del* subcommand.
It is followed by one or more package names or patterns.

List packages
-------------
The *ls* or *list* subcommand list the content of the repository.
It can be followed by a possibly empty list of patterns which are
used as patters following the Unix file globbing syntax. That of
course means you probably need to quote metacharacters to prevent
the shell from expanding them. If no patterns are listed on the
commandline the whole repository is listed.

It takes the following options:

 -f, --format <template>
  Use `template` to format the output of a single package. It can
  contain placeholders of the form *{* <name> *}* where <name> is a
  debian control file field, i.e. Maintainer, Version, ...

  In addition to standard debian control fields, the following
  can be used as well:

  component
    the component the package is in
  release
    the codename of the release
  Filename
    the filename relative the the repository root directory

  Actually, the template is directly used as a python format string,
  so by using e.g. ``{Package:20}`` the package name will always be
  at least 20 characters wide and left aligned inside that width.
  If the number is preceded by ``>`` the package name will be right
  aligned. With ``=`` it will be centered instead.

  The usual backslash escape sequences, i.e. \\a, \\b. \\f. \\n, \\r,
  \\t and \\v insert the ascii control characters  BEL, BS, FF, LF,
  CR, TAB, VT resp.

  Furthermore, \\xhh with
  hh being exactly two hex digits will insert a character with
  the given hex value. \\uhhhh with 4 hex digits inserts the
  unicode 16 bit codepoint etc.

 -p, --pattern <pattern>
  List packages matching the given patterns. Shell globbing syntax
  is used. Useful to prevent shell expansion of the pattern, when
  given in the ``-pfoo*f`` or ``--pattern=*bar`` form. This option
  can be repeated several times.

Move packages
-------------
Moving is a convenience method in case either some packages went to
the wrong place or the repository layout changes. The same effect
could be achieved by fetching the packages using apt, delete them
with ``debrep del`` and readd them with ``debrep add``.
It needs at least one of the following options:

 --tr <release> target release
 --tc <compoonent> target component

The remaining options are names of packages that are to be moved.

If only a target release is given, packages are moved from one
release to the other, but keeping their componenent. Packages
where the component does not exist in the target release will
not be moved and generate error messaages.

If only a target component is given, packages from the given
release (or the default release) are moved from their current
component to the target. If the target comonent does not exist
in one of the releases, the release remains unchanged and an
error message is generated.

EXAMPLES
========

:debrep add foo.deb
   Add foo.deb and bar.deb to the default release, default component.

Project Homepage at https://github.com/nilsrennebarth/debrep
