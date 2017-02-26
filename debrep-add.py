#!/usr/bin/env python3
'''
Add a package to the repository
'''

import debrep.config
from debrep.db.sqlite import Db

config = debrep.config.Config()

db = Db(config)

