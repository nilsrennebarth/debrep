#!/usr/bin/env python3
'''
Debrep module implementing sqlite3 as db backend
'''

import sqlite3

class Db:

	_tables = [
		'''CREATE TABLE packages (
		id INTEGER PRIMARY KEY AUTOINCREMENT,
		name TEXT,
		control TEXT,
		Version TEXT,
		Architecture TEXT,
		udeb INTEGER,
		Filename TEXT,
		Size INTEGER,
		MD5Sum TEXT,
		SHA1 TEXT,
		SHA256 TEXT,
		Description_md5 TEXT
		)''',
		'''CREATE TABLE releases (
		id INTEGER PRIMARY KEY AUTOINCREMENT,
		Codename TEXT
		)''',
		'''CREATE TABLE release_pkg (
		idrel INTEGER,
		comp TEXT,
		idpkg INTEGER,
		PRIMARY KEY (idrel, idpkg)
		)''',
		'''CREATE TABLE release_src (
		idrel INTEGER,
		comp TEXT,
		idsrc INTEGER,
		PRIMARY KEY (idrel, idsrc)
		)''',
		'''CREATE TABLE dbschema (
		version INTEGER
		)'''
	]
		
	def __init__(self, config):
		self.db = sqlite3.connect(**config.db)
		self.dbc = self.db.cursor()
		self.mktables()

	def mktables(self):
		for sql in Db._tables:
			self.dbc.execute(sql)
