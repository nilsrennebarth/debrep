#!/usr/bin/env python3
"""
Debrep module implementing sqlite3 as db backend
"""

import collections
import logging
import os
import os.path
import sqlite3


from debian.deb822 import Deb822
from package import BinPkgRef

logger = logging.getLogger(__name__)

#
# Query utility functions
#

def condParaAdd(conds, paras, colname, v):
	"""Append condition and parameters depending on length of v
	"""
	if len(v) == 0:
		return
	if len(v) == 1:
		conds.append(colname+"=?")
	else:
		conds.append(colname+" IN (?"+ ",?" * (len(v)-1) + ")")
	paras += v

def condParaAddStr(conds, paras, colname, v):
	"""
	Append condition and parameters for String comparison with globs
	"""
	def hasGlobs(str):
		"""Test if string contains globbing special characters"""
		for i in "*?[]":
			if i in str: return True
		return False

	def singleCond(str):
		"""Create a single globbing or equal condition from a string"""
		return colname + (' GLOB ?' if hasGlobs(str) else '=?')

	if len(v) == 0:
		return
	paras += v
	cond = ' OR '.join(map(singleCond, v))
	if len(v) > 1:
		cond = '(' + cond + ')'
	conds.append(cond)

def makeQuery(arch, component, idrel, name):
	"""
	Create a query from a standard set of properties

	Given a list of architectures, components, release ids
	and name globs, create query fragments and a parameter
	list. An empty list as usual means no restrictions on the
	given property.

	Return a tuple with the join fragment, the where fragment
	and the query parameters
	"""
	sqlparams = [];
	cond = [];
	condParaAdd(cond, sqlparams, 'b.Architecture', arch)
	condParaAdd(cond, sqlparams, 'r.component', component)
	condParaAdd(cond, sqlparams, 'r.idrel', idrel)
	condParaAddStr(cond, sqlparams, 'b.name', name)
	sqlj = ' FROM binpackages b JOIN release_bin r on b.id=r.idpkg '
	if len(cond) > 0:
		sqlw = ' WHERE ' + ' AND '.join(cond)
	else:
		sqlw = ''
	return sqlj, sqlw, sqlparams


class Db:

	version = 1

	def mktables(self):
		logger.info('Create new db')
		file = "{dir}/sqlite-{ver:03d}.sql".format(
			dir=os.path.dirname(__file__), ver=self.version
		)
		with open(file) as f:
			self.dbc.executescript(f.read())
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
		if self.dbc.fetchone() is None:
			# No, table does not exist. Assume db is empty
			self.mktables()
			return
		self.dbc.execute("SELECT version FROM dbschema")
		dbv = self.dbc.fetchone()[0]
		logger.debug('Opened db version %d', dbv)

	def __init__(self, config):
		dbfile = config.db['database']
		if not os.path.exists(dbfile):
			os.makedirs(os.path.dirname(dbfile), exist_ok=True)
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
			name, control, Version, Architecture, udeb,
			Size, MD5Sum, SHA1, SHA256, Description_md5)
		VALUES (
			:name, :control, :Version, :Architecture, :udeb,
			:Size, :MD5Sum, :SHA1, :SHA256, :Description_md5)
		"""
		self.dbc.execute(sql, pkg.__dict__);
		pkg.id = self.dbc.lastrowid
		logger.info("New binary package %s_%s_%s with id %d",
			pkg.name, pkg.Version, pkg.Architecture, pkg.id)

	def replaceBinary(self, pkg, idrel, component, filename):
		"""
		Replace entry for a binary package with new data

		This again is just the low-level method without checks
		"""
		sql = """UPDATE binpackages
		SET name=:name, control=:control, Version=:Version,
			Architecture=:Architecture, Size=:Size, MD5Sum=:MD5Sum,
			SHA1=:SHA1, SHA256=:SHA256, Description_md5=:Description_md5
		WHERE id=:id
		"""
		self.dbc.execute(sql, pkg.__dict__);
		sql = """UPDATE release_bin SET Filename=?, component=?
		WHERE idrel=? AND idpkg=?
		"""
		self.dbc.execute(sql, (filename, component, idrel, pkg.id))
		logger.info("Replace binary package %s_%s with version %s",
			pkg.name, pkg.Architecture, pkg.Version)

	def getBinary(self, pkgid):
		"""
		Get a binary package from the database as a dictionary
		"""
		self.dbc.execute('SELECT * FROM binpackages WHERE id=?', (pkgid,))
		r = self.dbc.fetchone()
		return dict(zip(r.keys(), r))

	def binGetRefs(self, pkgid):
		"""
		Get all references to a binary package
		"""
		self.dbc.execute(
			"""SELECT p.id, r.idrel, rl.Codename, r.component, r.Filename,
				p.name, p.Version, p.Architecture, p.SHA256
			FROM binpackages p
			JOIN release_bin r ON p.id = r.idpkg
			JOIN releases rl ON r.idrel = rl.id
			WHERE p.id=?""", (pkgid,))
		result = []
		for row in self.dbc.fetchall():
			result.append(BinPkgRef(**dict(zip(row.keys(), row))))
		logger.debug("binGetRefs: refs for %d: \n- %s" % (pkgid,
			"\n- ".join([str(x) for x in result])))
		return result

	def binDelRef(self, pkgid, relid):
		"""
		Delete a binary package from a release

		Return a list of references to the package. The first reference in the
		list is the reference that just has been deleted. It will be marked with
		the property 'deleted' set to True.
		"""
		# Before deleting the references, get it, otherwise the Filename
		# and component from the reference is lost. Also get all other refs
		# because the caller may need them.
		result = self.binGetRefs(pkgid)
		# delete the reference
		self.dbc.execute(
			"""DELETE FROM release_bin
			WHERE idrel=? AND idpkg=?""", (relid, pkgid))
		if len(result) == 0:
			# Only happens on concurrent access
			logger.warning("While deleting package id %d: Not found", pkgid)
			return result
		if len(result) == 1:
			# That was the last reference to that package
			# Safety check in case the ref has been deleted in the meantime
			if result[0].id == pkgid and result[0].idrel == relid:
				self.dbc.execute("DELETE from binpackages WHERE id=?", (pkgid,))
				logger.debug("Last reference to %s deleted",
					result[0].Filename)
				result[0].deleted = True
			else:
				result[0].deleted = False
			return result
		# Search the deleted reference and move it to the front
		for pos, x in enumerate(result):
			if x.id == pkgid and x.idrel == relid:
				x.deleted = True
				logger.debug("Delete %s_%s from %s/%s", x.name, x.Version,
					x.Codename, x.component)
				break
		if pos == 0:
			return result
		if 'deleted' in result[pos].__dict__:
			result.insert(0, result.pop(pos))
		else:
			result[0].deleted = False
		return result

	def relName(self, id):
		"""
		Codename of a release given as id
		"""
		c = self.db.cursor()
		c.execute('SELECT Codename FROM releases WHERE id=?', (id,))
		return (c.fetchone())[0]

	def getrefsAdd(self, pkg, tid):
		"""
		Get all references needed when adding a package to a target release.

		Those references are:
		- a Package with the same name and arch in the target
		  relese
		- Packages with the same name, arch and version in
		  releases other than the target release

		Returns a list of all references, starting with the one in the
		target release if found there at all
		"""
		self.dbc.execute(
			"""SELECT id, r.idrel, r.component, r.Filename, name, Version,
				Architecture, SHA256
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
		sql = """SELECT b.*, r.Filename
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


	def listBin(self, arch, component, idrel, name):
		"""
		Return an iterator over packages.
		arch, component and relese can all be either None, meaning
		no restriction, a string or number (in case of idrel),
		or an iterable.
		"""
		(sqlj, sqlw, sqlparams) = makeQuery(arch, component, idrel, name)
		sql = 'SELECT b.*,rel.Codename AS release, r.component, r.Filename ' \
			  + sqlj \
			  + ' JOIN  releases rel on r.idrel = rel.id ' \
			  + sqlw \
			  + ' ORDER BY rel.Codename, r.component, b.name, b.Architecture'
		logger.debug("Query for list = %s", sql)
		self.dbc.execute(sql, sqlparams)
		while True:
			r = self.dbc.fetchone()
			if r is None: return
			# make a dict from the query in the usual way
			p = collections.defaultdict(lambda: '', zip(r.keys(), r))
			# update with keys from control file
			p.update(Deb822(p['control']))
			del p['control']
			p['shortdesc'] = (p['Description'].partition('\n'))[0]
			yield p

	def listIds(self, arch, component, idrel, name):
		"""
		List package ids for given properties

		Again, properties are given as a list of arch, component, releaseids
		and names, the latter might also be globs. An empty property means
		no restriction, otherwise eeach list is ORed and all three
		properties ANDed.

		Return a list of package ids.
		"""
		(sqlj, sqlw, sqlparams) = makeQuery(arch, component, idrel, name)
		sql = 'SELECT b.id ' \
			  + sqlj \
			  + sqlw
		self.dbc.execute(sql, sqlparams)
		return [row[0] for row in self.dbc.fetchall()]

	def addBinaryRef(self, idrel, idpkg, component, filename):
		self.dbc.execute(
			"""INSERT OR IGNORE INTO release_bin
			   (idrel, idpkg, component, Filename)
			VALUES (?, ?, ?, ?)""", (idrel, idpkg, component, filename))

	def delBinaryRef(self, id, idrel):
		self.dbc.execute(
			'DELETE FROM release_bin WHERE idrel=? AND idpkg=?',
			(idrel, id))

	def close(self):
		self.dbc.close()
		self.db.commit()
		self.db.close()

