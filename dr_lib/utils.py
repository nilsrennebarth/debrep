#!/usr/bin/env python3
"""
debrep utilities
"""
import codecs
import collections
import hashlib
import re

def sum():
	"""
	A new hash function that simply computes the size
	"""
	class summer():
		def __init__(self):
			self.sum = 0
		def update(self, b):
			self.sum += len(b)
		def hexdigest(self):
			return str(self.sum)

	return summer()

class Hashes(collections.namedtuple('Hashes', 'Size MD5Sum SHA1 SHA256')):
	def __str__(self):
		return 'Hashes(\n ' \
			+ '\n '.join(map(lambda x: x + ' = '+ getattr(self, x), \
							 self._fields)) \
			+ '\n)'

class Hasher:
	"""
	Compute various hashes and the size in parallel
	"""
	def __init__(self):
		self.dgst = (sum(), hashlib.md5(), hashlib.sha1(), hashlib.sha256())

	def update(self, buf):
		for d in self.dgst:
			d.update(buf)

	def digest(self):
		return Hashes._make([d.hexdigest() for d in self.dgst])

	@staticmethod
	def hash(path):
		h = Hasher()
		with open(path, 'rb') as f:
			while True:
				buf = f.read(8192)
				if len(buf) == 0: break
				h.update(buf)
		return h.digest()


_ESCAPE_SEQUENCE_RE = re.compile(r'''
    ( \\U........      # 8-digit hex escapes
    | \\u....          # 4-digit hex escapes
    | \\x..            # 2-digit hex escapes
    | \\[0-7]{1,3}     # Octal escapes
    | \\N\{[^}]+\}     # Unicode characters by name
    | \\[\\'"abfnrtv]  # Single-character escapes
    )''', re.UNICODE | re.VERBOSE)

def decodeEscapes(s):
	"""
	Decode escape sequences in a string, i.e. do something similar
	to what the python literal parser does: \n to LF, \t to TAB ...

	Taken from http://stackoverflow.com/questions/
	4020539/process-escape-sequences-in-a-string-in-python

	The problem is, that unicode_escape will convert to latin1,
	so we must make sure to only apply it where necessary, and
	that are all matches of the escape sequences we wish to
	convert.
	"""
	def decodeMatch(match):
		return codecs.decode(match.group(0), 'unicode-escape')

	return _ESCAPE_SEQUENCE_RE.sub(decodeMatch, s)



if __name__ == '__main__':
	import sys
	print(Hasher.hash(sys.argv[1]))
