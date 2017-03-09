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
- export a release, i.e. creation of files and indices in a an apt-get-able
  way, given a base path.


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

TODO
----
- write and update changed indices, sign the release
- commandline args parsing
  - add a -c --config option to take the configuration from
  - use a general argument parser and a (sub-) command specific one
- listings
- check architecture
- delete packages
- copy release
- Move between components
- source Packages
- new db and store implementations:
  - a release store, hardlink based
  - a mysql database backend



Database
--------
Tables

- Packages (for .deb and .udeb)
- Sources
- Releases

Packages
~~~~~~~~
Hold all binary Packages, i.e. over all distributions. It will held .deb and
.udeb Packages and all associated data. Column ``control`` will hold the full
text of the debian control file. ``Version`` and ``Architecture`` are the same as
the version field from the control field, it is present to allow searches on
the database level.  ``udeb`` is 0 for normal packages, 1 for udeb
packages. ``Filename``, ``Size``, and the checksums are the same as the fields of
the same name in a Packages file. The SHA256 in particular is to check if a
package with the same name, version and architecture is already present.

Table definition::

  CREATE TABLE binpackages (
    id INT PRIMARY KEY AUTOINCREMENT,
    name TEXT,
    control TEXT,
    Version TEXT,
    Architecture TEXT,
    udeb INT,
    Filename TEXT,
    Size INT,
    MD5Sum TEXT,
    SHA1 TEXT,
    SHA256 TEXT,
    Description_md5 TEXT
  )

Releases
~~~~~~~~
Hold a Release, i.e. the meta data of a relase::

  CREATE TABLE releases (
    id INT PRIMARY KEY AUTOINCREMENT,
    Codename TEXT,
  )

The information what packages belong to a release is held in separate tables
because these are lists::

  CREATE TABLE release_pkg (
    idrel INT,
    component TEXT,
    idpkg INT,
    PRIMARY KEY (idrel, idpkg)
  )

  CREATE TABLE release_src (
    idrel INT,
    component TEXT,
    idsrc INT,
    PRIMARY KEY (idrel, idsrc)
  )



Schema
~~~~~~
Hold database metadata. Currently only a version number that needs to be
increased each time the table definitions are changed. In that case,
a corresponding update script must be applied. Table::

  CREATE TABLE dbschema (
    version INT
  )




Configuration items
-------------------
For a release

- Description, Label, Version, Suite, Codename

For the repository

- File storage strategy. pool, bydist
- Create "Contents" indices.
- Allow distributions with equal package version but different content

Configuration is a yaml file structured as follows:

Toplevel is a Mapping with keys

  root
    Path to repository root directory (optional)
    If not given, the default depends on where the config file was found:

      location specific
        the current working dir itself i.e. ``.``
      user specific
        ``~/public_html/repo``
      global
        ``/var/www/repo``
  db
    Arguments to connect to the database. This is a mapping
    optional if dbtype is sqlite, in this case the path to the
    database defaults to `root`/``db/repo.db``
  dbtype
    One of sqlite or mysql. Optionsal, default is sqlite
  layout
    One of pool or bydist. Optional, default is pool
  defgpgkey
    default GPG key to sign the releases with.
    Optional, if omitted, defaults to the user's first secret key.
  defrelease
    Name of the default release to add to if none is given.
    Optional, default is the first writeable release
  defarchitectures
    A set of architectures. Optional, default is {all, amd64, i386}
  indexcompressors
    A set of compression methods to use for compressing the indices.
    Possible values none, gz, bz2, xz. Default { gz, xz }
  indexarchall
    True means to create a separate index for architecture 'all'
    packages and omit those from the architecture specific indices.
    This is the default. False means to merge architeture 'all'
    packages into the architecture specific indices.
  releases
    A sequence of releases, each a mapping

A release is a mapping with keys

  name
    Codename of the release. Must be unique
  suite
    Suite name, i,e, an alias of the release (optional)
  version
    Version number (optional)
  origin
    Origin of the release (optional)
  description
    optional description
  components
    sequence of strings. First one is the default for package
    operations
  architectures
    Set of strings. It is an error to add a binary package with an
    architecture not mentioned. Optional if defarchitectures is given.

The config file is named ``debrep.conf`` and is searched (in this order)

- location specific: in subdirectory ``config`` of the current working
  directory.
- user specific: in ``~/.config``
- global: in ``/etc/debrep/debrep.conf``

A config file must be found, and as soon as it is found, no further search is
done, in particular no attempt is made to merge specific with less specific
options.

Operations
----------
Database and file storage are plugins, so we need to define the
possible operations that need to be implemented.

Database
~~~~~~~~
Lowlevel ops:
- Enter new BinPackage to given release, component. Set id to
  newly generated one.
- Add existing Package id to release, component.
- Replace Package in release with different content
- Retrieve Package by id

- add a BinPackage to db. Parameters: release (primary name), component. 
  new means, a package of that name does not exist in the given release,
  and a package with the same content is not in the repo. The id must
  be -1 and it will be replaced by the new obtained during insert.
- add an existing BinPackage to db. Parameters: release, component. Package
  must have an id. A package with the same content is already present
  but not in the given release. Amounts to just adding the given
  (idrel, idpkg) pair to the release_pkg table

- del a BinPackage from db

on storage and db

Store
~~~~~
Filename encodes package,version,arch When using pools, all three determine
the content and packages whose version didn't change are shared across
releases.

For other storage strategies, we can lift the restriction that the same
version implies the same content and store a file under a release
specific path. Sharing files with the same content accross releases
can be done by using symlinks or hardlinks, but sharing can be switched
off as well.

Lowlevel ops:
- Add new file to store
- Add a new reference to an existing file
- Remove a reference to a file
- Remove the last reference to a file


Terminology
-----------

 component:
   A distribution is divided into one or more non-overlapping components.
   The division can be based on license as in debian, or on origin or
   maintainership, responsibility etc.
 distribution:
   Coherent collection of source and binary packages. Often synonymous with
   release.
