#!/usr/bin/env python3
"""
A repo file store holding files in a distribution component tree.
If the same package appears in sevaral distributions, symlinks
point to the file in the 'oldest' release, where older is determined
by the order of releases in the config file.
"""
import logging
import os
import os.path
import shutil

from basestore import BaseStore
from error import StoreError

logger = logging.getLogger(__name__)

def relname2symtarget(fname):
	"""Compute symlink target from package's relative name

	Given the Filename of a package relative the the repository root
	(which for this storage is dists/<release>/<component>/<pkgfilename>),
	compute the symlink target for all other files referencing the same
	package, .i. ../../<relase>/<component>/<pkgFilename>
	"""
	return os.path.join('..', '..', fname[len('dists/'):])


class Store(BaseStore):

	def __init__(self, config):
		super().__init__(config)
		self.db = config.getDb()
		self.releases = config.releases

	def pkgDir(self, pkg, component, release):
		"""Directory for the package, relative to the repository root"""
		return os.path.join('dists', release, component)

	def binAddRef(self, pkg, component, release):
		"""Add a new reference to a package

		Return the new filename
		"""
		self.binPrepareAdd(pkg, component, release)
		slist = Symreflist(self.releases, self.root)
		slist.setRefs(self.db.binGetRefs(pkg.id))
		slist.addRef(pkg, component, release)

	def binDelRef(self, refs):
		"""Remove a reference to a package"""
		slist = Symreflist(self.releases, self.root)
		slist.setRefs(refs)
		slist.delRef()


class Symreflist:
	"""
	Administer file data for a list of references

	There is one reference that holds the actual file, the
	primary reference, and all other are just symlinks to
	the primary reference.
	"""

	def __init__(self, releases, root):
		self.releases = releases
		self.root = root
		self.refs = []
		self.primaryRef = None

	def getPrimaryTarget(self):
		self.primaryTarget = relname2symtarget(self.primaryRef.Filename)

	def movePrimary(self, topos):
		"""
		Move the primary ref to the given position

		Move the file into the new position, then redirect all
		symlinks
		"""
		dst = self.refs[topos]
		if self.primaryRef is dst: return
		os.replace(self.primaryRef.abspath, dst.abspath)
		dst.islink = False
		self.primaryRef.islink = True
		self.primaryRef = dst
		self.getPrimaryTarget()
		for ref in self.refs:
			if not ref.islink: continue
			if os.path.exists(ref.abspath): os.remove(ref.abspath)
			os.symlink(self.primaryTarget, ref.abspath)

	def relno(self, release):
		"""Ordinal number of a release name"""
		return self.releases[release].no

	def setRefs(self, refs):
		if len(refs) == 0:
			raise StoreError('No references found' % pkg)
		for ref in refs:
			ref.abspath = os.path.join(self.root, ref.Filename)
			if os.path.islink(ref.abspath):
				# ref is symlink
				ref.islink = True
			else:
				# ref is real file
				if self.primaryRef is not None:
					# Only one ref must be a real file
					raise StoreError('Ref %s is real, symlink expected' % ref)
				self.primaryRef = ref
			self.refs.append(ref)
		if self.primaryRef is None:
			# At least one ref must be a real file
			raise StoreError('All refs of package %s are symlinks'
				% refs[0].pkgname())


	def addRef(self, pkg, component, release):
		"""Add reference to given package"""
		pkg.abspath = os.path.join(self.root, pkg.Filename)
		refs = self.refs
		# sort list in release order
		refs.sort(key=lambda ref: self.relno(ref.Codename))
		# Get index where new reference needs to be inserted
		for refpos in range(len(refs)+1):
			if refpos == len(refs): break
			if self.relno(release) == self.relno(refs[refpos].Codename):
				raise StoreError('Strange: %s already present in %s'
					% (pkg, release))
			if self.relno(release) < self.relno(refs[refpos].Codename): break
		if refpos > 0:
			pkg.islink = True
			# New ref is not in first release, i.e. becomes a symlink
			if self.primaryRef is refs[0]:
				# Primary ref is the right already, so create the right
				# symlink and we are done
				self.getPrimaryTarget()
				os.symlink(self.primaryTarget, pkg.abspath)
				return
			# Primary ref not the right one, move it
			logger.warning('Moving real file of %s to %s/%s',
				pkg.pkgname(), refs[0].Codename, refs[0].component)
			refs.append(pkg)
		else:
			refs.insert(0, pkg)
		self.movePrimary(0)

	def delRef(self):
		"""Delete the first reference"""
		d = self.refs[0]
		# sort list in release order
		self.refs.sort(key=lambda ref: self.relno(ref.Codename))
		if len(self.refs) > 1:
			if d is self.refs[0]:
				self.movePrimary(1)
			else:
				self.movePrimary(0)
		else:
			logger.debug("Delete package file %s", d.Filename)
		os.remove(d.abspath)

