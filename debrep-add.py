#!/usr/bin/env python3
'''
Add a package to the repository
'''

import logging, sys

from debrep import config, package
from debrep.store import pool

def addBinary(path, db, store):
	global config
	pkg = package.getBinFromDeb(path)
	logger.debug('Got package %s', str(pkg))
	release = config.defrelease
	rid = db.relId(release)
	if rid < 1:
		logger.error("Unknown release '%s'", config.defrelease)
		return
	(target, other) = db.getrefsAdd(pkg, rid)
	if target == None:
		db.newbinary(pkg)
		db.addbinref(pkg.id, rid)
	else:
		logger.info("Package %s already present", pkg.name)


#
# -------- main -------
#
logger = logging.getLogger('main')
logging.basicConfig(level=logging.DEBUG)

config = config.Config()
db = config.getDb()
store = config.getStore()
addBinary(sys.argv[1], db, store)
db.close()

# class BinPackage
#  construct from filename
#  compute checksums and size,
#  set properties like fields of the table 'Packages',
#  add current path
#  or construct from database entry
#  add method to write the Binary Package Index


# obtain control as Deb822 object as well as a string.
# compute hashes
# look up package in table packages, using name, version, architecture
# if found
#    if same content:
#        if in target: nothing to do
#        else: add id to target
#    else:
#        if exactly in target
#            replace existing
#        else:
#            if strict: refuse
#            else:
#                if in target: replace
#                else: add to target
#    return
# look up in table packages, using name, architecture
# if found
#    if not in target release: add to target
#    elif update_only and version < old_version: refuse
#    else:
#        remove old pkg from target
#        remove file if refcount == 0 (or move to morgue)
#        add new to target
