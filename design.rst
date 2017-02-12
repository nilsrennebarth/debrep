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

However, take a look at the python-debian package, the "official" module to
handle debian packages, changelogs, control files ...

To obtain a Deb822 object from a package, do

  from debian.debfile import DebFile
  d = DebFile('/var/cache/apt/archives/mini-dinstall_0.6.30ubuntu1_all.deb')
  c = d.debcontrol()

Now, c is a (subclass of a) dictionary.

  >>> c['depends']
  'python, python:any (<< 2.8), python:any (>= 2.7.5-5~), ...

To get more structured info about e.g. depends, do

  >>> from debian.deb822 import Package
  >>> p = Packages(c)
  >>> print(p.relations['depends'])
  [[{'arch': None, 'name': 'python', 've...
  >>> dep = p.relations['depends']
  >>> for i,r in enumerate(dep): print(i,r[0]['version'])
  0 None
  1 ('<<', '2.8')
  2 ('>=', '2.7.5-5~')
  3 ('>=', '0.7.93')
  4 None


Database
--------
Tables

- Packages (for .deb and .udeb)
- Sources
- Releases

Packages
~~~~~~~~
Hold all binary Packages, i.e. over all distributions. It will held .deb and
.udeb Packages and all associated data. Column `control` will hold the full
text of the debian control file. `Version` and `Architecture` are the same as
the version field from the control field, it is present to allow searches on
the database level.  `udeb` is 0 for normal packages, 1 for udeb
packages. `Filename`, `Size`, and the checksums are the same as the fields of
the same name in a Packages file. The SHA256 in particular is to check if a
package with the same name, version and architecture is already present.

  CREATE TABLE Packages (
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
    Description_md5 TEXT)

Releases
~~~~~~~~
Hold a Release, i.e. the meta data of a relase:

  CREATE TABLE Releases (
    id INT PRIMARY KEY AUTOINCREMENT,
    Version TEXT,
    Suite TEXT,
    Codename TEXT,
    Origin TEXT,
    Label TEXT,
    Components TEXT,
    Default_Component TEXT)

The information what packages belong to a release is held in separate tables
because these are lists:

  CREATE TABLE Release_pkg (
    idrel INT,
    comp TEXT,
    idpkg INT,
    PRIMARY KEY (idrel, idpkg)
  )

  CREATE TABLE Release_src (
    idrel INT,
    comp TEXT,
    idsrc INT,
    PRIMARY KEY (idrel, idsrc)
  )



Schema
~~~~~~
Hold database metadata. Currently only a version number that needs to be
increased each time the table definitions are changed. In that case,
a corresponding update script must be applied.

  CREATE TABLE Dbschema (
    version INT





Configuration items
-------------------
For a release

- Description, Label, Version, Suite, Codename

For the repository

- File storage strategy. pool, bydist
- Create "Contents" indices.
- Allow distributions with equal package version but different content

Terminology
-----------

 component:
   A distribution is divided into one or more non-overlapping components.
   The division can be based on license as in debian, or on origin or
   maintainership, responsibility etc.
 distribution:
   Coherent collection of source and binary packages. Often synonymous with
   release.
