import collections, os, yaml

class ConfigError(Exception):
	def __init__(self,msg):
		self._msg = msg
	def __str__(self):
		return self._msg

_top_options = [
	'db',
	'dbtype',
	'defarchitectures',
	'defrelease',
	'gpgkey',
	'layout',
	'root'
]

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
			if 'dbtype' not in cfg: cfg['dbtype'] = 'sqlite'
			if 'db' not in cfg and cfg['dbtype'] == 'sqlite':
				cfg['db'] = {
					'database':	os.path.join(cfg['root'], 'db', 'repo.db')
				}
			if 'defarchitectures' not in cfg:
				cfg['defarchitectures'] = [ 'amd64' ];
			if 'defrelease' not in cfg:
				cfg['defrelease'] = '?'
			if 'gpgkey' not in cfg:
				cfg['gpgkey'] = '?'
			if 'layout' not in cfg:
				cfg['layout'] = 'pool'

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
		for name in _top_options:
			setattr(self, name, config_dict[name])

				
