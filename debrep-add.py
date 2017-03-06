#!/usr/bin/env python3
'''
Add a package to the repository
'''

import logging, sys

from debrep import config, package
from debrep.store import pool

def addBinary(path, db, store, release, component):

	def searchContent(refs, checksum):
		for ref in refs:
			if ref.SHA256 == checksum: return ref.id
		return -1

	pkg = package.getBinFromDeb(path)
	logger.debug('Got package %s', str(pkg))
	rid = db.relId(release)
	if rid < 1:
		logger.error("Unknown release '%s'", config.defrelease)
		return
	refs = db.getrefsAdd(pkg, rid)
	id = searchContent(refs, pkg.SHA256)
	if id != -1:
		logger.debug('Package %s with given content found in repo', pkg.name)
		# The given content is already present in the repo
		# Is it already in the target release?
		if refs[0].idrel == rid:
			logger.info("Package '%s' with given content already present",
				pkg.name)
			return
		logger.info("Package '%s' with given content already in repo. Reusing",
			pkg.name)
		store.addBinaryRef(pkg)
		db.addBinaryRef(refs[0].id, rid)
		return
	# The given content is not present in the repo.
	# Can we add it at all? TODO: check if strict and if same version
	# already present in a release other than the target and refuse
	# Ok, we can add the package now. Do we need to replace an existing
	# package?
	if len(refs) > 0 and refs[0].idrel == rid:
		logger.debug('Need to replace %s_%s ', pkg.name, pkg.Version)
		# Yes, need to replace an existing package P_old
		# TODO refuse if upgradeOnly
		# Is P_old referenced elsewhere?
		if searchContent(refs[1:], refs[0].SHA256) != -1:
			logger.debug('Remove %s_%s from %s but keep it in repo',
				pkg.name, pkg.Version, release)
			# Yes it is, remove reference from target release.
			# Package will get a new id by default
			store.delBinaryRef(refs)
			db.delBinaryRef(refs[0].id, rid)
		else:
			logger.debug('Remove %s_%s from %s',
				pkg.name, pkg.Version, release)
			# Not it is not, remove it from store and recycle the
			# package id
			store.delBinaryLastRef(refs[0])
			pkg.id = refs[0].id
	# Now do an add or replace, depending on pkg.id
	if pkg.id == -1:
		store.addBinary(pkg)
		db.newBinary(pkg)
		db.addBinaryRef(pkg.id, rid)
		logger.info("Added package %s_%s to %s with new id %d",
			pkg.name, pkg.Version, release, pkg.id)
	else:
		store.addBinary(pkg)
		db.replaceBinary(pkg)
		logger.info("Added package %s_%s to %s under id %d",
			pkg.name, pkg.Version, release, pkg.id)



#
# -------- main -------
#
logger = logging.getLogger('main')
logging.basicConfig(level=logging.DEBUG)

config = config.Config()
db = config.getDb()
store = config.getStore()
addBinary(sys.argv[1], db, store, config.defrelease, '')
db.close()

