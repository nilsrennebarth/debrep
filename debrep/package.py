#!/usr/bin/env python3
"""
debrep Package classes

Contains the classes

 - BinPackage represent a binary package
 - SrcPackage represent a source package

"""

from types import SimpleNamespace
from numbers import Number
from debian.debfile import DebFile
from debian.deb822 import Deb822
import collections, hashlib


# Testing aid
if __name__ == '__main__':
	import os, sys
	sys.path.append(os.path.dirname(__file__))

import utils
from namedtuple_with_abc import namedtuple

class PkgError(Exception):
	def __init__(self,msg):
		self._msg = msg
	def __str__(self):
		return self._msg


class BinPackage (namedtuple.abc):
	'''
	Base class for binary packages
	'''
	_fields = [
		'name', 'control', 'cdict', 'Version',
		'Architecture', 'udeb', 'Filename', 'Size',
		'MD5Sum', 'SHA1', 'SHA256', 'Description_md5'
	]

	def __str__(self):
		keys = (
			'name', 'Version', 'Architecture', 'shortdesc', \
			'Size', 'SHA256', \
		)
		items = ('{}: {}'.format(k, getattr(self, k)) for k in keys)
		return '\n'.join(items)


	@property
	def shortdesc(self):
		return (self.cdict['Description'].partition('\n'))[0]

class BinPackageDeb(BinPackage):
	'''
	A binary package derived from a .deb file
	'''

	_fields = BinPackage._fields + ('debfile', 'origfile')

	def __str__(self):
		return super().__str__() + '\norigfile: ' + self.origfile


def getBinFromDeb(fname):
	'''
	Get a binary package from a .deb file
	'''
	dfile = DebFile(fname)
	cdict = dfile.debcontrol()
	csums = utils.get_hashes(fname)
	return BinPackageDeb(
		# General BinPackage properties
		name = cdict['Package'],
		control = dfile.control.get_content('control', 'utf-8'),
		cdict = dfile.debcontrol(),
		Version = cdict['Version'],
		Architecture = cdict['Architecture'],
		udeb = fname.endswith('.udeb'),
		Filename = '',
		Size = csums.size,
		MD5Sum = csums.md5,
		SHA1 = csums.sha1,
		SHA256 = csums.sha256,
		Description_md5 = hashlib.md5(
			cdict['Description'].encode() + b'\n').hexdigest(),
		# Special Deb properties
		debfile = dfile,
		origfile = fname
	)

class BinPackageDb(BinPackage):
	'''
	A binary package obtained from a database
	'''

	_fields = BinPackage._fields + ('id', )

	def __str__(self):
		return super().__str__() + '\nid: ' + str(self.id)

def getBinFromDb(db, pckid):
	'''
	Get a binary package from a database
	'''
	pdict = db.getbinary(pckid)
	pdict['cdict'] = Deb822(pdict['control'])
	return BinPackageDb(**pdict)

if __name__ == '__main__':
	fname = sys.argv[1]
	try:
		id = int(fname)
		fname = None
	except ValueError:
		pass
	if (fname != None):
		print(getBinFromDeb(arg))
	else:
		import config
		from db.sqlite import Db
		db = Db(config.Config())
		print(getBinFromDb(db, id))