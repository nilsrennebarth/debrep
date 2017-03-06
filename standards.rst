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

