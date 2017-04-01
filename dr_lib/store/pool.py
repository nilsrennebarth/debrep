#!/usr/bin/env python3
"""
Package pool implementation of a repo file store
"""
import logging, os, os.path, shutil

logger = logging.getLogger(__name__)

def pure_version(v):
	"""Version without the epoch"""
	(epoch, sep, version) = v.partition(':')
	return v if sep == '' else version

class Store:

	def __init__(self, config):
		self.root = config.root

	def pkgName(self, pkg):
		return pkg.name + '_' + pure_version(pkg.Version) + '_' \
		   + pkg.Architecture + '.deb'

	def pkgDir(self, pkg, component, release):
		base = pkg.name
		if 'Source' in pkg.cdict:
			base = pkg.cdict['Source']
			base = base.partition('(')[0].rstrip()
		if base.startswith('lib'):
			return os.path.join('pool', component, 'lib' + base[3], base)
		else:
			return os.path.join('pool', component, base[0], base)

	def addBinary(self, pkg, component, release):
		"""
		Add a new binary package to the store
		"""
		reldir  = self.pkgDir(pkg, component, release)
		relname = os.path.join(reldir, self.pkgName(pkg))
		# create directory
		os.makedirs(os.path.join(self.root, reldir), exist_ok=True)
		# copy file
		shutil.copy(pkg.origfile, os.path.join(self.root, relname))
		# write repository relative Filename to package
		pkg.Filename = relname

	def addBinaryRef(self, pkg, component, release):
		pass

	def delBinaryRef(self, refs):
		pass

	def delBinaryLastRef(self, ref):
		fname = os.path.join(self.root, ref.Filename)
		try:
			os.remove(fname)
		except FileNotFoundError:
			logger.warning("Removing %s: File not found", fname)

