import collections
import fnmatch
import importlib
import logging
import os
import types
import yaml

from error import ConfigError

logger = logging.getLogger(__name__)

_top_options = {
	'db': None,
	'dbtype': 'sqlite',
	'defarchitectures': set(['all', 'amd64', 'i386']),
	'defcomponents': [ 'main' ],
	'defcomponentrules': None,
	'defrelease': None,
	'defgpgkey': None,
	'store': 'pool',
	'root': None,
	'releases': None
}

_release_options = {
	'name': None,
	'suite': 'testing',
	'version': None,
	'origin': None,
	'description': None,
	'components': None,
	'componentrules': None,
	'architectures': None,
	'readonly': False,
	'gpgkey': None
}

def _del_unknowns(orig, proto):
	for k in [x for x in orig.keys()]:
		if k not in proto:
			logger.warning('Unknown key "%s" in config, ignored' % k)
			del orig[k]
	return orig

def getConfig(args):

	def tryconf(path):
		nonlocal config_dict
		fname = os.path.join(path, 'debrep.conf')
		if not os.path.exists(fname):
			return False
		else:
			with open(fname) as f:
				config_dict = yaml.safe_load(f)
			return True

	def set_general_defaults(cfg):
		# merge in default values
		for k, v in _top_options.items():
			if not hasattr(cfg, k): setattr(cfg, k, v)
		if cfg.dbtype == 'sqlite' and cfg.db is None:
			cfg.db = {'database':	os.path.join(cfg.root, 'db', 'repo.db')}

	def set_release_defaults(rel):
		# merge in default values
		for k, v in _release_options.items():
			if not hasattr(rel, k): setattr(rel, k, v)
		# set yet unspecified values from top config
		if rel.architectures is None:
			rel.architectures = top.defarchitectures
		if rel.components is None:
			rel.components = top.defcomponents
		if rel.gpgkey is None:
			rel.gpgkey = top.defgpgkey

	def local_defaults(cfg):
		if not hasattr(cfg, 'root'):
			cfg.root = os.getcwd()

	def user_defaults(cfg):
		if not hasattr(cfg, 'root'):
			cfg.root = os.path.expanduser('~/public_html/repo')

	def global_defaults(cfg):
		if not hasattr(cfg, 'root'):
			cfg.root = '/var/www/repo'

	def set_releases(cfg):
		releases = collections.OrderedDict()
		no = 0
		for r in cfg.releases:
			release = Release(**(_del_unknowns(r, _release_options)))
			release.no = no
			no += 1
			releases[release.name] = release
			set_release_defaults(release)
		# Replace the original array of dicts obtained from yaml
		# by the new ordered dict just created
		cfg.releases = releases

	config_dict = {}
	if args.config is not None:
		if not tryconf(args.config):
			raise ConfigError('File not found: %s ' % file)
		set_specific_defaults = local_defaults
	elif tryconf('.'):
		set_specific_defaults = local_defaults
	elif tryconf(os.path.expanduser('~/.config')):
		set_specific_defaults = user_defaults
	elif tryconf('/etc/debrep'):
		set_specific_defaults = global_defaults
	else:
		raise ConfigError('No configuration found')
	top = Config(**(_del_unknowns(config_dict, _top_options)))
	set_specific_defaults(top)
	set_general_defaults(top)
	set_releases(top)
	# only now can we determine the default release if not already set
	if top.defrelease is None:
		for release in top.releases.values():
			if realease.readonly: continue
			top.defrelease = release
	else:
		if top.defrelease not in top.releases:
			raise ConfigError("Unknown defrelease '%s'" % top.defrelease)
		top.defrelease = top.releases[top.defrelease]
	# too verbose
	# logger.debug("Config:\n %s", str(top))
	return top




class Config(types.SimpleNamespace):
	"""
	Configuration for debrep
	"""
	def getDb(self):
		if '_db' in self.__dict__: return self._db
		if self.dbtype not in ('sqlite'):
			raise ConfigError("Unknown dbtype '{}'".format(self.dbtype))
		db = importlib.import_module('db.' + self.dbtype)
		self._db = db.Db(self)
		return self._db

	def getStore(self):
		if '_store' in self.__dict__: return self._store
		if self.store not in ('pool', 'symtree'):
			raise ConfigError("Unknown store '{}'".format(self.store))
		store = importlib.import_module('store.' + self.store)
		self._store = store.Store(self)
		return self._store

	def getPkgComponent(self, name, release):
		"""Get configured component of a package

		The configuration can specify release specific or global rules to
		automatically place a package in a certain component. This method
		implements the rules.
		"""
		fallback = release.components[0]
		rules = release.componentrules \
			or self.defcomponentrules
		if rules is None: return fallback
		for rule in rules:
			for pattern in rule['packages']:
				if fnmatch.fnmatch(name, pattern): return rule['component']
		return fallback

class Release(types.SimpleNamespace):
	"""
	Configuration for a relase in repository
	"""
	pass
