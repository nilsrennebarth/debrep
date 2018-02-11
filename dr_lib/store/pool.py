#!/usr/bin/env python3
"""
Package pool implementation of a repo file store
"""
import logging
import os.path

from basestore import BaseStore

logger = logging.getLogger(__name__)

class Store(BaseStore):

	def pkgDir(self, pkg, component, release):
		"""Directory for the package, relative to the repository root"""
		# The debian pool dir is based on the package's source name
		base = pkg.sourceName()
		# Take the first letter as an additional subdir (or the first
		# four letters if the name starts with "lib")
		prefixlen = 4 if base.startswith('lib') else 1
		return os.path.join('pool', component, base[0:prefixlen], base)

	def binAddRef(self, pkg, component, release):
		self.binPrepareAdd(pkg, component, release)

	def binDelRef(self, refs):
		if len(refs) != 1: return
		if not refs[0].deleted: return
		self.binDelCleanup(os.path.join(self.root, refs[0].Filename))

