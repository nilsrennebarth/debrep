#!/usr/bin/env python3
"""
Debrep module implementing sqlite3 as db backend
"""

import logging, sqlite3

from debian.deb822 import Deb822
from package import BinPkgRef

logger = logging.getLogger(__name__)

class DbError(Exception):
	def __init__(self,msg):
		self._msg = msg
	def __str__(self):
		return self._msg

class Db:

	version = 1

	_tables = [
		"""CREATE TABLE binpackages (
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
		)""",
		"""CREATE INDEX bpname ON binpackages (name, Architecture)
		""",
		"""CREATE TABLE srcpackages (
		id INTEGER PRIMARY KEY AUTOINCREMENT,
		name TEXT,
		dsc TEXT,
		Directory TEXT,
		Priority TEXT,
		Section TEXT
		)
		""",
		"""CREATE TABLE releases (
		id INTEGER PRIMARY KEY AUTOINCREMENT,
		Codename TEXT
		)""",
		"""CREATE UNIQUE INDEX relcodename ON releases (Codename)""",
		"""CREATE TABLE release_bin (
		idrel INTEGER,
		component TEXT,
		idpkg INTEGER,
		PRIMARY KEY (idrel, idpkg)
		)""",
		"""CREATE INDEX rbpr ON release_bin (idpkg, idrel)
		""",
		"""CREATE TABLE release_src (
		idrel INTEGER,
		component TEXT,
		idsrc INTEGER,
		PRIMARY KEY (idrel, idsrc)
		)""",
		"""CREATE TABLE dbschema (
		version INTEGER
		)"""
	]

	def mktables(self):
		logger.info('Create new db')
		for sql in Db._tables:
			self.dbc.execute(sql)
		self.dbc.execute('INSERT INTO dbschema VALUES (:v)', dict(v=Db.version))
		self.db.commit()

	def syncreleases(self, releases):
		"""
		Synchronize releases with those enumerated in the config

		If a release mentioned in the config exists, its id is set to the
		one obtained from db. If a relase mentioned in the config is not
		in the db, it is created and its id set to the newly created one.
		If a release is in the db but not in the config, we will generate
		a warning, but leave it to the user to actually delete it.
		"""
		# First get all releases from the database and set id in config
		self.dbc.execute('SELECT id,Codename FROM releases')
		for row in self.dbc.fetchall():
			id, name = row
			if name in releases:
				releases[name].id = id
			else:
				logger.warning("Relase with codename %s exists in the "
					"database but not in the configuration. You might want "
					"to purge it from the database", name)
		# Next create all releases new in config
		for release in releases.values():
			if hasattr(release, 'id'): continue
			self.dbc.execute(
				"""INSERT INTO releases (Codename) VALUES (?)""",
				(release.name,)
			)
			release.id = self.dbc.lastrowid

	def initdb(self):
		"""
		Make database ready for queries. If none of our tables
		exist, create them. Otherwise get the version and eventually
		update it to the current one.
		"""
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
		self.syncreleases(config.releases)

	def newBinary(self, pkg):
		"""
		Create a new entry for a binary package

		This is the low-level method that justs creates an
		entry, without performing any checks.
		"""
		sql = """INSERT INTO binpackages (
			name, control, Version, Architecture, udeb, Filename,
			Size, MD5Sum, SHA1, SHA256, Description_md5)
		VALUES (
			:name, :control, :Version, :Architecture, :udeb, :Filename,
			:Size, :MD5Sum, :SHA1, :SHA256, :Description_md5)
		"""
		self.dbc.execute(sql, pkg.__dict__);
		pkg.id = self.dbc.lastrowid
		logger.info("New binary package %s_%s_%s with id %d",
			pkg.name, pkg.Version, pkg.Architecture, pkg.id)

	def replaceBinary(self, pkg):
		"""
		Replace entry for a binary package with new data

		This again is just the low-level method without checks
		"""
		sql = """UPDATE binpackages
		SET name=:name, control=:control, Version=:Version, Filename=:Filename,
			Architecture=:Architecture, Size=:Size, MD5Sum=:MD5Sum,
			SHA1=:SHA1, SHA256=:SHA256, Description_md5=:Description_md5
		WHERE id=:id
		"""
		self.dbc.execute(sql, pkg.__dict__);
		logger.info("Replace binary package %s_%s with version %s",
			pkg.name, pkg.Architecture, pkg.Version)

	def getBinary(self, pkgid):
		"""
		Get a binary package from the database as a dictionary
		"""
		self.dbc.execute('SELECT * FROM binpackages WHERE id=?', (pkgid,))
		r = self.dbc.fetchone()
		return dict(zip(r.keys(), r))

	def relName(self, id):
		"""
		Codename of a release given as id
		"""
		c = self.db.cursor()
		c.execute('SELECT Codename FROM releases WHERE id=?', (id,))
		return (c.fetchone())[0]

	def getrefsAdd(self, pkg, tid):
		"""
		Get all references needed when adding a package.

		Those references are:
		- a Package with the same name and arch in the target
		  relese
		- Packages with the same name, arch and version in
		  releases other than the target release

		Returns a list of all references, starting with the one in the
		target release if found there at all
		"""
		self.dbc.execute(
			"""SELECT id, r.idrel, r.component, name, Version, Architecture,
				Filename, SHA256
			FROM binpackages p
			JOIN release_bin r ON p.id = r.idpkg
			WHERE p.name=:name AND p.Architecture=:arch
			AND (r.idrel=:tid OR p.Version=:version)
			""", dict(name=pkg.name, arch=pkg.Architecture,
				tid=tid, version=pkg.Version))
		result = []
		rels = set()
		for row in self.dbc.fetchall():
			ref = BinPkgRef(**dict(zip(row.keys(), row)))
			if ref.idrel in rels:
				# must not happen
				raise DbError("Release %s contains several versions "
					"of %s_%s", self.relName(ref.idrel), pkg.name,
					pkg.Architecture)
			if ref.idrel == tid:
				# Found in target release
				result.insert(0, ref)
			else:
				# Found in other release
				result.append(ref)
		return result

	def getIndex(self, arch, component, idrel, with_all=False):
		"""
		Return an iterator over all packages in an arch,comp,release
		triple. A package is returned as a dict where the keys are the
		column names of the binpackages table.
		"""
		sql = """SELECT b.*
			FROM release_bin r
			JOIN binpackages b ON r.idpkg=b.id
			WHERE r.idrel=? AND r.component=?
				AND b.Architecture {}
			ORDER BY b.name
			""".format("IN ('all', ?)" if with_all else "= ?")
		self.dbc.execute(sql, (idrel, component, arch))
		while True:
			r = self.dbc.fetchone()
			if r is None: return
			yield dict(zip(r.keys(), r))

	def condParaAdd(self, conds, paras, colname, v):
		"""Append condition and parameters depending on type of v
		"""
		if len(v) == 0:
			return
		if len(v) == 1:
			conds.append(colname+"=?")
		else:
			conds.append(colname+" IN (?"+ ",?" * (len(v)-1) + ")")
		paras += v

	def listBin(self, arch, component, idrel, name):
		"""
		Return an iterator over packages.
		arch, component and relese can all be either None, meaning
		no restriction, a string or number (in case of idrel),
		or an iterable.
		"""
		sql = """SELECT b.*,rel.Codename AS release, r.component
		FROM release_bin r
		JOIN binpackages b on r.idpkg=b.id
		JOIN releases rel on r.idrel = rel.id
		"""
		sqlparams = [];
		cond = [];
		self.condParaAdd(cond, sqlparams, "b.Architecture", arch)
		self.condParaAdd(cond, sqlparams, "r.component", component)
		self.condParaAdd(cond, sqlparams, "r.idrel", idrel)
		if len(name) == 1:
			cond.append("b.name GLOB ?")
			sqlparams += name
		elif len(name) > 1:
			c = "(b.name GLOB ? " + " OR b.name GLOB ?" * (len(name)-1) + ")"
			cond.append(c)
			sqlparams += name
		if len(cond) > 0:
			sql += " WHERE " + " AND ".join(cond)
		sql += " ORDER BY rel.Codename, r.component, b.Architecture, b.name"
		self.dbc.execute(sql, sqlparams)
		while True:
			r = self.dbc.fetchone()
			if r is None: return
			# make a dict from the query in the usual way
			p = dict(zip(r.keys(), r))
			# update with keys from control file
			p.update(Deb822(p['control']))
			del p['control']
			yield p

	def addBinaryRef(self, id, component, idrel):
		self.dbc.execute(
			"""INSERT OR IGNORE INTO release_bin (idrel, component, idpkg)
			VALUES (?, ?, ?)""", (idrel, component, id))

	def delBinaryRef(self, id, idrel):
		self.dbc.execute(
			'DELETE FROM release_bin WHERE idrel=? AND idpkg=?',
			(idrel, id))

	def close(self):
		self.dbc.close()
		self.db.commit()
		self.db.close()

