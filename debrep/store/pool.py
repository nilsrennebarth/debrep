#!/usr/bin/env python3
'''
Package pool implementation of a repo file store
'''
import os, shutil
from pathlib import PurePath

def pure_version(v):
	'''Version without the epoch'''
	(epoch, sep, version) = v.partition(':')
	return v if sep == None else version

class Store:

	def __init__(self, config):
		self.root = config.root

	def pkgName(self, pkg):
		return ''.join(pkg.name, '_', pure_version(pkg.version), '_',
					   pkg.Architecture, '.deb')

	def pkgDir(self, pkg):
		base = pkg.name
		if 'Source' in pkg.cdict: base = pkg.cdict['Source']
		if base.startswith('lib'):
			return PurePath('pool', 'lib' + base[3], base)
		else:
			return PurePath('pool', base[0], base)

	def addBinary(self, pkg):
		shutil.copy(pkg.origfile, PurePath(self.root, self.pkgDir(pkg)),
			self.pkgName(pkg))

	def addBinaryRef(self, pkg):
		pass

	def delBinaryRef(self, pkg):
		pass

	def delBinaryLastref(self, pkg):
		os.remove(PurePath(self.root, pkg.Filename))

