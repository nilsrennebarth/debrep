import collections, importlib, os, yaml

class ConfigError(Exception):
	def __init__(self,msg):
		self._msg = msg
	def __str__(self):
		return self._msg

_top_options = {
	'db': None,
	'dbtype': 'sqlite',
	'defarchitectures': ['i386', 'amd64'],
	'defrelease': ['testing'],
	'gpgkey': None,
	'store': 'pool',
	'root': None,
	'releases': None
}

class Config:
	"""
	Configuration for debrep
	"""

	def __init__(self, rootdir=None):

		def readconf(fname):
			nonlocal config_dict
			with open(fname) as f:
				config_dict = yaml.safe_load(f)
			
		def tryconf(path):
			fname = os.path.join(path, 'debrep.conf')
			if not os.path.exists(fname):
				return False
			else:
				readconf(fname)
				return True

		def general_defaults(cfg):
			for k, v in _top_options.items():
				if k not in cfg: cfg[k] = v
			if cfg['dbtype'] == 'sqlite' and cfg['db'] == None:
				cfg['db'] = {
					'database':	os.path.join(cfg['root'], 'db', 'repo.db')
				}

		def local_defaults(cfg):
			if 'root' not in cfg:
				cfg['root'] = os.getcwd()

		def user_defaults(cfg):
			if 'root' not in cfg:
				cfg['root'] = os.path.expanduser('~/public_html/repo')

		def global_defaults(cfg):
			if 'root' not in cfg:
				cfg['root'] = '/var/www/repo'

		config_dict = {}
		if tryconf('./config'):
			setdefs = local_defaults
		elif tryconf(os.path.expanduser('~/.config')):
			setdefs = user_defaults
		elif tryconf('/etc/debrep'):
			setdefs = global_defaults
		else:
			raise ConfigError('No configuration found')
		setdefs(config_dict)
		general_defaults(config_dict)
		for name in _top_options.keys():
			setattr(self, name, config_dict[name])

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

