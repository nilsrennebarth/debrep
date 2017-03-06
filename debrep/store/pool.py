#!/usr/bin/env python3
'''
Package pool implementation of a repo file store
'''
import os, os.path, shutil

def pure_version(v):
	'''Version without the epoch'''
	(epoch, sep, version) = v.partition(':')
	return v if sep == '' else version

class Store:

	def __init__(self, config):
		self.root = config.root

	def pkgName(self, pkg):
		return pkg.name + '_' + pure_version(pkg.Version) + '_' \
		   + pkg.Architecture + '.deb'

	def pkgDir(self, pkg):
		base = pkg.name
		if 'Source' in pkg.cdict: base = pkg.cdict['Source']
		if base.startswith('lib'):
			return os.path.join('pool', 'lib' + base[3], base)
		else:
			return os.path.join('pool', base[0], base)

	def addBinary(self, pkg):
		'''
		Add a new binary package to the store
		'''
		reldir  = self.pkgDir(pkg)
		relname = os.path.join(reldir, self.pkgName(pkg))
		# create directory
		os.makedirs(os.path.join(self.root, reldir), exist_ok=True)
		# copy file
		shutil.copy(pkg.origfile, os.path.join(self.root, relname))
		# write repository relative Filename to package
		pkg.Filename = relname

	def addBinaryRef(self, pkg):
		pass

	def delBinaryRef(self, pkg):
		pass

	def delBinaryLastRef(self, pkg):
		os.remove(os.path.join(self.root, pkg.Filename))

