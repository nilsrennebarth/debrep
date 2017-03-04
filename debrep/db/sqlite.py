#!/usr/bin/env python3
'''
Debrep module implementing sqlite3 as db backend
'''

import logging, sqlite3

logger = logging.getLogger(__name__)

class Db:

	version = 1

	_tables = [
		'''CREATE TABLE binpackages (
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
		'''CREATE TABLE srcpackages (
		id INTEGER PRIMARY KEY AUTOINCREMENT,
		name TEXT,
		dsc TEXT,
		Directory TEXT,
		Priority TEXT,
		Section TEXT
		)
		''',
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

	def mktables(self):
		logger.info('Create new db')
		for sql in Db._tables:
			self.dbc.execute(sql)
		self.dbc.execute('INSERT INTO dbschema VALUES (:v)', dict(v=Db.version))
		self.db.commit()

	def initdb(self):
		'''
		Make database ready for queries. If none of our tables
		exist, create them. Otherwise get the version and eventually
		update it to the current one.
		'''
		# query sqlite if table 'dbschema' exists
		self.dbc.execute("SELECT name FROM sqlite_master "
			"WHERE type='table' AND name='dbschema'")
		if self.dbc.fetchone() == None:
			# No, table does not exist. Assume db is empty
			self.mktables()
			return
		self.dbc.execute("SELECT version FROM dbschema")
		dbv = self.dbc.fetchone()[0]
		logger.debug('Opened db version %d', dbv)
		
	def __init__(self, config):
		self.db = sqlite3.connect(**config.db)
		self.db.row_factory = sqlite3.Row
		self.dbc = self.db.cursor()
		self.initdb()

	def newbinary(self, pkg):
		'''
		Create a new entry for a binary package

		This is the low-level method that justs creates an
		entry, without performing any checks.
		'''
		sql = '''INSERT INTO binpackages (
			name, control, Version, Architecture, udeb, Size,
			MD5Sum, SHA1, SHA256, Description_md5)
		VALUES (
			:name, :control, :Version, :Architecture, :udeb, :Size,
			:MD5Sum, :SHA1, :SHA256, :Description_md5)
		'''
		self.dbc.execute(sql, pkg._asdict());
		pkg.id = self.dbc.lastrowid
		logger.info("New binary package %s_%s_%s with id %d",
			pkg.name, pkg.Version, pkg.Architecture, pkg.id)
		self.db.commit()

	def replacebinary(self, pkg):
		'''
		Replace entry for a binary package with new data

		This again is just the low-level method without checks
		'''
		sql = '''UPDATE binpackages
		SET name=:name, control=:control, Version=:Version,
			Architecture=:Architecture, Size=:Size, MD5Sum=:MD5Sum,
			SHA1=:SHA1, SHA256=:SHA256, Description_md5=:Description_md5
		WHERE id=:id
		'''
		self.dbc.execute(sql, pkg._asdict());
		logger.info("Replace binary package %s_%s with version %s",
			pkg.name, pkg.Architecture, pkg.Version)

	def getbinary(self, pkgid):
		'''
		Get a binary package from the database as a dictionary
		'''
		self.dbc.execute('SELECT * FROM binpackages WHERE id=?', (pkgid,))
		r = self.dbc.fetchone()
		return dict(zip(r.keys(), r))
		
	def close(self):
		self.dbc.close()
		self.db.close()

