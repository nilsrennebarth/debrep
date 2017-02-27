#!/usr/bin/env python3
'''
Add a package to the repository
'''

import debrep.config
from debrep.db.sqlite import Db

config = debrep.config.Config()

db = Db(config)

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
