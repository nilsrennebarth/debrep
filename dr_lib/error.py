#!/usr/bin/env python3
"""
Debrep error classes
"""

class DebrepError(Exception):
	"""
	debrep base error class
	"""
	def __init__(self, msg):
		self._msg = msg
	def __str__(self):
		return self._msg

class ArgError(DebrepError): pass
class DbError(DebrepError): pass
class ConfigError(DebrepError): pass
class PkgError(DebrepError): pass
class StoreError(DebrepError): pass
