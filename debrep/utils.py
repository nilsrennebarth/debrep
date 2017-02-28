#!/usr/bin/env python3
"""
debrep utilities
"""
import collections, hashlib

class Hashes(collections.namedtuple('Hashes', 'size md5 sha1 sha256')):
	def __str__(self):
		return 'Hashes(\n ' \
			+ '\n '.join(map(lambda x: x + ' = '+ str(getattr(self, x)), \
							 self._fields)) \
			+ '\n)'

def get_hashes(path):
	dgst = (hashlib.md5(), hashlib.sha1(), hashlib.sha256())
	with open(path, 'rb') as f:
		buf = f.read(8192)
		size = len(buf)
		while len(buf):
			for d in dgst:
				d.update(buf)
			buf = f.read(8192)
			size += len(buf)
	return Hashes._make([size] + [d.hexdigest() for d in dgst])

if __name__ == '__main__':
	import sys
	print(get_hashes(sys.argv[1]))
