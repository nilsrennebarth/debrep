#!/usr/bin/env python3
"""
debrep Package classes

Contains the classes

 - BinPackage represent a binary package
   - BinPackageDeb package from .deb file
   - BinPackageDb package from database
 - SrcPackage represent a source package

"""
import hashlib
import os
import types
import utils

from debian.debfile import DebFile
from debian.deb822 import Deb822

# Testing aid
if __name__ == '__main__':
	import sys
	sys.path.append(os.path.dirname(__file__))


class BinPackage (types.SimpleNamespace):
	"""
	Base class for binary packages
	"""
	def __str__(self):
		keys = (
			'name', 'Version', 'Architecture', 'shortdesc',
			'Size', 'SHA256',
		)
		items = ('{}: {}'.format(k, getattr(self, k)) for k in keys)
		return '\n'.join(items)

	@property
	def shortdesc(self):
		return (self.cdict['Description'].partition('\n'))[0]

	def sourceName(self):
		"""The source name of a package

		If the package has a "Source" key, it is the package's source
		name (except for a possible version number of course). Otherwise
		it is the package's name
		"""
		if 'Source' in self.cdict:
			return self.cdict['Source'].partition('(')[0].rstrip()
		else:
			return self.name

	def poolDir(self):
		"""Directory containing the package in a debian package pool

		These are just the last two directory components, i.e. the part
		that is release and component independent.
		"""
		base = self.sourceName()
		prefixlen = 4 if base.startswith('lib') else 1
		return os.path.join(base[0:prefixlen], base)


class BinPackageDeb(BinPackage):
	"""
	A binary package derived from a .deb file
	"""
	def __str__(self):
		return super().__str__() + '\norigfile: ' + self.origfile

def getBinFromDeb(fname):
	"""
	Get a binary package from a .deb file
	"""
	dfile = DebFile(fname)
	cdict = dfile.debcontrol()
	result = BinPackageDeb(
		id = -1,
		name = cdict['Package'],
		control = dfile.control.get_content('control', 'utf-8'),
		cdict = dfile.debcontrol(),
		Version = cdict['Version'],
		Architecture = cdict['Architecture'],
		udeb = fname.endswith('.udeb'),
		Description_md5 = hashlib.md5(
			cdict['Description'].encode() + b'\n').hexdigest(),
		debfile = dfile,
		origfile = fname
	)
	result.__dict__.update(utils.Hasher.hash(fname)._asdict())
	return result


class BinPackageDb(BinPackage):
	"""
	A binary package obtained from a database
	"""
	def __str__(self):
		return super().__str__() + '\nid: ' + str(self.id) \
			+ '\nFilename: ' + self.Filename

def getBinFromDb(db, pckid):
	"""
	Get a binary package from a database
	"""
	pdict = db.getbinary(pckid)
	pdict['cdict'] = Deb822(pdict['control'])
	return BinPackageDb(**pdict)

class BinPkgRef(types.SimpleNamespace):
	"""
	A reference to a binary package

	Holds the following data from a binary package reference:

	- id: package id
	- idrel: release id
	- Codename: code name of release
	- component: component the package is part of
	- Filename: file name of package relative to repository root
	- name: package name
	- Version: package version
	- Architecture: package architecture
	- SHA256: sha256 checksum of package
	"""

	strformat = "{name}-{Version}({Architecture} in {Codename}/{Component}"
	pkgformat = "{name}-{Version}/{Architecture}"

	def __str__(self):
		return BinPkgRef.strformat.format_map(self.__dict__)

	def pkgname(self):
		return BinPkgRef.strformat(format_map(self.__dict__)



if __name__ == '__main__':
	fname = sys.argv[1]
	try:
		id = int(fname)
		fname = None
	except ValueError:
		pass
	if (fname is not None):
		print(getBinFromDeb(fname))
	else:
		import config
		from db.sqlite import Db
		db = Db(config.Config())
		print(getBinFromDb(db, id))
