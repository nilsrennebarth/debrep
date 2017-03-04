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
import hashlib


# Testing aid
if __name__ == '__main__': sys.path.append(os.path.dirname(__file__))

import utils

class PkgError(Exception):
	def __init__(self,msg):
		self._msg = msg
	def __str__(self):
		return self._msg

class BinPackage(SimpleNamespace):

	def __init__(self, arg):
		if isinstance(arg, Number):
			self.fromdb(arg)
		elif isinstance(arg, str):
			self.frompath(arg)
		else:
			raise PkgError('Invalid argument type')

	def __str__(self):
		keys = (
			'name', 'Version', 'Architecture', 'Shortdesc', \
			'Size', 'SHA256', 'Origfile' \
		)
		items = ('{}: {}'.format(k, self.__dict__[k]) for k in keys)
		return '\n'.join(items)

	def fromdb(self, arg):
		# not yet implemented
		pass

	def frompath(self, arg):
		self.debfile = DebFile(arg)
		self.cdict = self.debfile.debcontrol()
		self.id = -1
		self.name = self.cdict['Package']
		self.control = self.debfile.control.get_content('control', 'utf-8')
		self.Version = self.cdict['Version']
		self.Architecture = self.cdict['Architecture']
		# let us keep this simple for now
		self.udeb = arg.endswith('.udeb')
		(self.Size, self.MD5Sum, self.SHA1, self.SHA256) = \
			utils.get_hashes(arg)
		self.Description_md5 = hashlib.md5( \
			self.cdict['Description'].encode() + b'\n' \
		).hexdigest()
		self.Origfile = arg
		self.Shortdesc = (self.cdict['Description'].partition('\n'))[0]

if __name__ == '__main__':
	print(BinPackage(sys.argv[1]))

