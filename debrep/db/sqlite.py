#!/usr/bin/env python3
'''
Debrep module implementing sqlite3 as db backend
'''

import logging, sqlite3

logger = logging.getLogger(__name__)

class DbError(Exception):
	def __init__(self,msg):
		self._msg = msg
	def __str__(self):
		return self._msg

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
		'''CREATE INDEX bpname ON binpackages (name, Architecture)
		''',
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
		'''CREATE UNIQUE INDEX relcodename ON releases (Codename)''',
		'''CREATE TABLE release_bin (
		idrel INTEGER,
		comp TEXT,
		idpkg INTEGER,
		PRIMARY KEY (idrel, idpkg)
		)''',
		'''CREATE INDEX rbpr ON release_bin (idpkg, idrel)
		''',
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

	def relId(self, name):
		self.dbc.execute('SELECT id FROM releases WHERE Codename=?', (name,))
		r = self.dbc.fetchone()
		return -1 if r == None else r[0]

	def mkreleases(self, releases):
		'''
		Create releases enumerated in the config

		If a release with the given name does not exist it will be
		created now. We don't delete any that we don't find in the
		config.
		'''
		for release in releases:
			if self.relId(release['name']) < 1:
				self.dbc.execute(
					'''INSERT INTO releases (Codename) VALUES (?)''',
					(release['name'],)
				)

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
		logger.debug('Configured releases: %s', str(config.releases))
		self.mkreleases(config.releases)

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

	def relName(self, id):
		'''
		Codename of a release given as id
		'''
		c = self.db.cursor()
		c.execute('SELECT Codename FROM releases WHERE id=?', (id,))
		return (c.fetchone())[0]

	def getrefsAdd(self, pkg, tid):
		'''
		Get all references needed when adding a package.

		Those references are:
		- Packages with the same name, arch and version in
		  releases other than the target release
		- Packages with the same name and arch in the target
		  relese
		'''
		self.dbc.execute(
			'''SELECT id, r.idrel, name, Version, Architecture, SHA256
			FROM binpackages p
			JOIN release_bin r ON p.id = r.idpkg
			WHERE p.name=:name AND p.Architecture=:arch
			AND (r.idrel=:tid OR p.Version=:version)
			''', dict(name=pkg.name, arch=pkg.Architecture,
				tid=tid, version=pkg.Version))
		targetref = None
		otherrefs = {}
		for row in self.dbc.fetchall():
			rowdict = dict(zip(row.keys(), row))
			if row['idrel'] == tid:
				# Found in target release
				if targetref == None:
					targetref = rowdict
				else:
					raise DbError("Release %s contains several versions "
						"of %s_%s", self.relName(tid), pkg.name,
						pkg.Architecture)
			else:
				# Found in other release
				rid = row['idrel']
				if rid not in otherrefs:
					otherrefs[rid] = rowdict
				else:
					raise DbError("Release %s contains several versions "
						"of %s_%s", self.relName(rid), pkg.name,
						pkg.Architecture)
		return (targetref, otherrefs)

	def addbinref(self, id, relid):
		self.dbc.execute(
			'INSERT OR IGNORE INTO release_bin (idrel, idpkg) VALUES (?, ?)',
			(relid, id))

	def close(self):
		self.dbc.close()
		self.db.commit()
		self.db.close()

