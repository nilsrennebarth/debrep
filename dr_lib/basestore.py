#!/usr/bin/env python3
"""
Base class for a store.

A store maintains the actual debian packages in the filesystem.
Packages can be added and removed from the store. Packages are
always added or removed from a store before being added or removed
from the database.

A store implements the following methods:

  __init__(self, config) : optional
    Initialization. All data needed from the passed config must be
    copied into the object.

    In the BaseStore only config.root is copied

  pkgDir(self, pkg, component, release) : mandatory
    Given a package object, component and release, return the directory
    the package will be placed in, relative to the repository root

  binNewPkg(self, pkg, component, release) : optional
    Add a new package to the repository with the given component and
    release. The package does not yet exist in the repository.
    Must add the `Filename` property to the pkg object, holding
    the name of the package relative to the repository root.

    In the BaseStore, the package's name and directory are computed,
    pkg.Filename is set and the file is physically copied into the
    repository.

  binAddRef(self, pkg, component, release) : mandatory
    Add a new reference to the package. Will only be called if the
    package is already present in the repository and only a new
    reference to it is added. pkg.Filename must be set as in
    binNewPkg

  binDelRef(self, refs) : mandatory
    Delete a reference. A list of BinPkgRef objects is passed to the
    method. The first item of the list is the reference to be deleted.
    The list may contain a single item only, in that case the last
    reference to the package is deleted, which usually means, the
    file is removed

"""
import logging
import os
import os.path
import shutil

logger = logging.getLogger(__name__)

class BaseStore:

	def __init__(self, config):
		self.root = config.root

	def binNewPkg(self, pkg, component, release):
		self.binPrepareAdd(pkg, component, release)
		# copy file
		shutil.copy(pkg.origfile, os.path.join(self.root, pkg.Filename))


	# Helper methods useful for all child classes

	def pkgFilename(self, pkg):
		"""Filename for the package"""
		# Get version without a possible epoch
		version = pkg.Version[pkg.Version.find(':')+1 : ]
		return '_'.join([pkg.name, version, pkg.Architecture + '.deb'])

	def binPrepareAdd(self, pkg, component, release):
		"""
		Prepare adding a binary package to the given release and component

		The method will compute the paths, create necessary directories
		and finally set the `Filename` attribute of pkg to the filname
		of the package relative to the repository root,

		The directory where the package will be put in is computed by
		the implementation specific method pkgDir that takes the same
		arguments as this method
		"""
		reldir  = self.pkgDir(pkg, component, release)
		# create directory
		os.makedirs(os.path.join(self.root, reldir), exist_ok=True)
		pkg.Filename = os.path.join(reldir, self.pkgFilename(pkg))

	def binDelCleanup(self, filename):
		"""
		Remove the given file, cleaning up now empty directories

		filename is an absolute path and supposed to be in a subdir
		of self.root
		"""
		try:
			os.remove(filename)
		except FileNotFoundError:
			logger.warning("Removing %s: File not found", filename)
		while True:
			filename = os.path.dirname(filename)
			# stop at repo root
			if filename == self.root: break
			# Simply try to remove the directory. Stop if an error occurs,
			# meaning either the directory is not empty or e.g. permissions
			# are missing
			try:
				os.rmdir(filename)
			except OSError:
				break

