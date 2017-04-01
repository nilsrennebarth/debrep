#!/usr/bin/env python3
"""
debrep utilities
"""
import collections, hashlib

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


if __name__ == '__main__':
	import sys
	print(Hasher.hash(sys.argv[1]))
