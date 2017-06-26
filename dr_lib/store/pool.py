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

	def __init__(self, config, db):
		self.root = config.root
		# this store does not need access to the database

	def pkgFilename(self, pkg):
		"""Filename for the package"""
		return pkg.name + '_' + pure_version(pkg.Version) + '_' \
		   + pkg.Architecture + '.deb'

	def pkgDir(self, pkg, component, release):
		"""Directory for the package, relative to the repository root"""
		return os.path.join('pool', component, pkg.poolDir())

	def binNewPkg(self, pkg, component, release):
		"""Add a new binary package to the store

		Return the new Filename
		"""
		reldir  = self.pkgDir(pkg, component, release)
		relname = os.path.join(reldir, self.pkgFilename(pkg))
		# create directory
		os.makedirs(os.path.join(self.root, reldir), exist_ok=True)
		# copy file
		shutil.copy(pkg.origfile, os.path.join(self.root, relname))
		return relname

	def binAddRef(self, pkg, component, release):
		return os.path.join(
			self.pkgDir(pkg, component, release),
			self.pkgFilename(pkg)
		)

	def binDelRef(self, refs):
		pass

	def binDelLastRef(self, ref):
		fname = os.path.join(self.root, ref.Filename)
		try:
			os.remove(fname)
		except FileNotFoundError:
			logger.warning("Removing %s: File not found", fname)

