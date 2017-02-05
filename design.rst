Design goals
============

Debian repository management. Create a standard apt-get'able Repository of
debian packages, containing a mix of unchanged debian packages and own
packages.

Requirements:

- Quick generation of indices, i.e. use a database, and packages must be
  added explicitly (which may of course mean copied to a special "incoming"
  directory.
- Do not use a database server, i.e. use either sqlite or some other
  file-based database.
- primary commandline, possibly a browser based frontend
- plug-ins for database and repository organisation, the latter meaning, where
  the package files actually end up, and how the same package ends up in
  several distributions (symlink, hardlink, copy, or all files share the same
  location, as is the case with the normal package pool)
- Support to directly add packgages to the archive, i.e. without a .changes
  file
- logging mechanism
- adding, removing distributions, possibly held configuration in database as
  well as config files.
- possibly hold two different contents of a name, version, arch triple, but
  will need a file path strategy different from the pools.

Possible feature ideas, taken from reprepro

- Move no longer needed files from repository to a "morgue"
- import from other repositories using apt
- Support source packages, deb and udeb
- check free space before downloads
- as we use gpg from the commandline, we need to be able to specify its
  home, most probably in a configuration setting
- allow to specify package listing output by using a template of some kind,
  probably something wich directly comes with pyton. In addition to the normal
  Variables given by the debian specified fields of a package, some more might
  be useful, e.g. id, architecture, component, type (i.e. deb, udeb, dsc), and
  distribution, It also might be useful, to split the filename into at least
  basedir (of the whole repository), directory leading to the file, and the
  filename itself.
- Allow some filtering on results, syntax still up to discussion, possibly
  just a python expression, + regex and globs.
- Maybe additions/removals according to debian dependencies
- implement incoming mechanism, using .changes files.
- handle override files
- copy or move packages between distributions.
- snapshots
  

Existing software
-----------------

  dak
    needs a database server and apparently disallows addding packages
    without .changes

  mini-dak
    no db at all

  reprepro
    Done in C, strange commandline syntax and uses berkeley db

  mini-dinstall
    disallows adding without .changes, no pools, no database,
    uses apt-ftparchive to generate indices.

  debarchiver
    seems too simple, uses perl


We might take some useful code from mini-dinstall: DpkgControl which parses a
dpkg control file (together with the other classes it depends on:
DpkgDatalist minidistall.SignedFile, OrderedDict, minidinstall.SafeWriteFile),
Dnotify to support an incoming directory and ChangeFile

So what we basically do is, to extend mini-dinstall to hava a databbase in
the background and to several file store backends plus distribution
administration commands.
