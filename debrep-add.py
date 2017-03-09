#!/usr/bin/env python3
'''
Add a package to the repository
'''

import logging, sys

from debrep import config, index, package
from debrep.store import pool

def getRelease(relname):
	if relname in config.releases:
		return config.releases[relname]
	else:
		logger.error("Unknown release '%s'", relname)
		return None

def addBinary(path, db, store, component, relname):

	def searchContent(refs, checksum):
		for ref in refs:
			if ref.SHA256 == checksum: return ref.id
		return -1

	pkg = package.getBinFromDeb(path)
	logger.debug('Got package %s', str(pkg))
	release = getRelease(relname)
	if release == None: return
	if component == None: component = release.components[0]
	# TODO check if component is part of release
	refs = db.getrefsAdd(pkg, release.id)
	id = searchContent(refs, pkg.SHA256)
	if id != -1:
		logger.debug('Package %s with given content found in repo', pkg.name)
		# The given content is already present in the repo
		# Is it already in the target release?
		if refs[0].idrel == release.id:
			logger.info("Package '%s' with given content already present",
				pkg.name)
			return
		logger.info("Package '%s' with given content already in repo. Reusing",
			pkg.name)
		store.addBinaryRef(pkg, component, relname)
		db.addBinaryRef(refs[0].id, component, release.id)
		return
	# The given content is not present in the repo.
	# Can we add it at all? TODO: check if strict and if same version
	# already present in a release other than the target and refuse
	# Ok, we can add the package now. Do we need to replace an existing
	# package?
	if len(refs) > 0 and refs[0].idrel == release.id:
		logger.debug('Need to replace %s_%s ', pkg.name, pkg.Version)
		# Yes, need to replace an existing package P_old
		# TODO refuse if upgradeOnly
		# Is P_old referenced elsewhere?
		if searchContent(refs[1:], refs[0].SHA256) != -1:
			logger.debug('Remove %s_%s from %s but keep it in repo',
				pkg.name, pkg.Version, relname)
			# Yes it is, remove reference from target release.
			# Package will get a new id by default
			store.delBinaryRef(refs)
			db.delBinaryRef(refs[0].id, release.id)
		else:
			logger.debug('Remove %s_%s from %s',
				pkg.name, pkg.Version, relname)
			# Not it is not, remove it from store and recycle the
			# package id
			store.delBinaryLastRef(refs[0])
			pkg.id = refs[0].id
	# Now do an add or replace, depending on pkg.id
	if pkg.id == -1:
		store.addBinary(pkg, component, relname)
		db.newBinary(pkg)
		db.addBinaryRef(pkg.id, component, release.id)
		logger.info("Added package %s_%s to %s/%s with new id %d",
			pkg.name, pkg.Version, relname, component, pkg.id)
	else:
		store.addBinary(pkg, component, relname)
		db.replaceBinary(pkg)
		logger.info("Added package %s_%s to %s/%s under id %d",
				pkg.name, pkg.Version, relname, component, pkg.id)


def updateIndices(db, arch, component, relname):
	release = getRelease(relname)
	if release == None: return
	idx = index.BinIndexer(arch, component, relname, config.root)
	idx.create(
		db.getIndex(arch, component, release.id)
	)

#
# -------- main -------
#
logger = logging.getLogger('main')
logging.basicConfig(level=logging.DEBUG)

config = config.getConfig()
db = config.getDb()
store = config.getStore()

if sys.argv[1] == 'add':
	addBinary(sys.argv[2], db, store, None, config.defrelease)
elif sys.argv[1] == 'idx':
	updateIndices(db, 'amd64', 'main', config.defrelease)

db.close()

