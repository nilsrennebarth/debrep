======================
 Summary of standards
======================

Debian
======


Repository Format
-----------------
The Binary Package Index has a paragraph for each Package. This is
the Package's control file with the additional fields:

  Filename
    path of file relative to repository base directory
  Size
    size of .deb in bytes
  MD5Sum, SHA1, SHA256
    Checksums of .deb as lowercase hex string
  Description-md5
    MD5 checksum of the Description, starting with the second byte
    after 'Description:', and ending with the trailing newline.

As the python Deb822 class strips the final newline of a field, you need
to readd it to obtain the correct sum::

  a = DebFile('/home/nils/tmp/0ad_0.0.17-1_amd64.deb')
  cd = a.debcontrol()
  hashlib.md5(cd['Description'].encode()+b'\n').hexdigest()


For a given release, there is one index per (arch, comp, compression),
where arch runs over all architectures supported by the repo plus 'all'
Packages with architecture 'all' may be contained in the Index
for the binary architectures as well, for older clients.

Compression should contain at least on of none, .gz, .bz2, the official
debian mirror has .gz and .xz Strangely enough, uncompressed is mentioned
in the Release, but not present

For each index, there are 3 entries in the Release file, for md5, SHA1, SHA256

The following items are indexed in a Release file:

- Contents, per (component,arch) in dists/<component>/Contents-<arch>
- Packages, per (component, arch) in dists/<component>/binary-<arch>/Packages
- Translations, per (component,lang) in dists/<component>/i18n/

A translation index is like a Packages index but with the following
fields only:

- Package
- Description-md5
- Description-$LANG


Sources
~~~~~~~
Sources are mostly like an additional architecture, i.e. there is an index per
release and component.

A source is stored in the repository as a Debian source control file
(``.dsc``) and the file referenced in it by the Files multiline field. All
files will be stored in the same directory. The fields of the .dsc file will
appear in the packages file and must thus be stored in the database.

Code Snippets
-------------

However, take a look at the python-debian package, the "official" module to
handle debian packages, changelogs, control files ...

To obtain a Deb822 object from a package, do::

  from debian.debfile import DebFile
  d = DebFile('/var/cache/apt/archives/mini-dinstall_0.6.30ubuntu1_all.deb')
  c = d.debcontrol()


Now, c is a (subclass of a) dictionary. ::

  >>> c['depends']
  'python, python:any (<< 2.8), python:any (>= 2.7.5-5~), ...

A string of the control file can be obtained via::

  d.control.get_content('control', 'utf-8')

Do version comparisons via apt_pkg.version_compare(a, b)
To get more structured info about e.g. depends, do::

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

gpg invocations to sign release files::

  echo "$PASSPHRASE" \
    | gpg --no-tty --batch --passphrase-fd=0 --default-key "$KEYID" \
      --detach-sign -o Release.gpg.tmp "$1"
   echo "$PASSPHRASE" \
     | gpg --no-tty --batch --passphrase-fd=0 --default-key "$KEYID" \
       --clearsign -o InRelease.tmp "$1"


In python, without passphrase::

   import subprocess
   res = subprocess.run(['gpg', '--no-tty', '--batch', '--default-key',
     'debrep', '--clearsign', '-o', 'test.conf.inline', 'test.conf'])
   res = subprocess.run(['gpg', '--no-tty', '--batch', '--default-key',
     'debrep', '--detach-sign', '-o', 'test.conf.gpg', 'test.conf'])

 Listing of releases in sqlite3::

   select r.Codename, b.component, p.id, name, Version
   from release_bin b
   join binpackages p on b.idpkg = p.id
   join releases r on b.idrel = r.id

Parse the release file using::

    with open('Release', 'r') as f:
        rel = debian.deb822.Deb822(f)
    for l in rel['SHA256'].splitlines();
        (hash, size, file) = l.split()

Then, the file can be added to the list with given hash and size,
All has to be repeated for MD5Sum and SHA1 as well.
