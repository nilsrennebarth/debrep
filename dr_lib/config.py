import collections, importlib, logging, os, types, yaml

logger = logging.getLogger(__name__)

class ConfigError(Exception):
	def __init__(self,msg):
		self._msg = msg
	def __str__(self):
		return self._msg

_top_options = {
	'db': None,
	'dbtype': 'sqlite',
	'defarchitectures': set(['all', 'amd64', 'i386']),
	'defcomponents': [ 'main' ],
	'defrelease': ['testing'],
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
	'architectures': None,
	'readonly': False,
	'gpgkey': None
}

def _del_unknowns(orig, proto):
	for k in orig.keys():
		if k not in proto: del orig[k]
	return orig

def getConfig(file=None):

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
		if cfg.dbtype == 'sqlite' and cfg.db == None:
			cfg.db = {'database':	os.path.join(cfg.root, 'db', 'repo.db')}

	def set_release_defaults(rel):
		# merge in default values
		for k, v in _release_options.items():
			if not hasattr(rel, k): setattr(rel, k, v)
		# set yet unspecified values from top config
		if rel.architectures == None:
			rel.architectures = top.defarchitectures
		if rel.components == None:
			rel.components = top.defcomponents
		if rel.gpgkey == None:
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
		for r in cfg.releases:
			release = Release(**(_del_unknowns(r, _release_options)))
			releases[release.name] = release
			set_release_defaults(release)
		# Replace the original array of dicts obtained from yaml
		# by the new ordered dict just created
		cfg.releases = releases

	config_dict = {}
	if file != None:
		if not tryconf(file):
			raise ConfigError('File not foud: %s ' % file)
		set_specific_defaults = local_defaults
	elif tryconf('./config'):
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
	logger.debug("Config:\n %s", str(top))
	return top




class Config(types.SimpleNamespace):
	"""
	Configuration for debrep
	"""
	def getDb(self):
		if self.dbtype not in ('sqlite'):
			raise ConfigError("Unknown dbtype '{}'".format(self.dbtype))
		db = importlib.import_module('db.' + self.dbtype)
		return db.Db(self)

	def getStore(self):
		if self.store not in ('pool'):
			raise ConfigError("Unknown store '{}'".format(self.store))
		store = importlib.import_module('store.' + self.store)
		return store.Store(self)

class Release(types.SimpleNamespace):
	'''
	Configuration for a relase in repository
	'''
	pass
