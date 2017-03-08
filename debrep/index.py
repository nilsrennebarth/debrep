#!/usr/bin/env python3
'''
Create an index file from an iterator that yields package ids
'''

import os, os.path
import bz2, lzma, zlib
from utils import Hasher, Hashes

class NoneCompressor:
	def compress(self, data): return data
	def flush(self): return b''

_supportedCompressors = {
	'none': NoneCompressor,
	'gz':   zlib.compressobj,
	'bz2':  bz2.BZ2Compressor,
	'xz':   lzma.LZMACompressor
}

class CsumCompressor:

	def __init__(self, basedir, basename, compressors):
		self.compressors = []
		self.filenames = []
		self.files = []
		self.csummers = []
		for cname in compressors:
			fname = basename
			if cname != 'none': fname += '.' + cname
			self.filenames.append(fname)
			self.files.append(open(os.path.join(basedir, fname), 'wb'))
			if cname == 'gz':
				compressor = (_supportedCompressors[cname])(wbits=31)
			else:
				compressor = (_supportedCompressors[cname])()
			self.compressors.append(compressor)
			self.csummers.append(Hasher())

	def write(self, s):
		for comp,hash,file in zip(self.compressors, self.csummers, self.files):
			c = comp.compress(s.encode())
			hash.update(c)
			file.write(c)

	def close(self):
		result = []
		for comp,hash,file,fname in zip(self.compressors, self.csummers,
									 self.files, self.filenames):
			c = comp.flush()
			hash.update(c)
			file.write(c)
			file.close()
			result.append((fname,) + hash.digest())
		return result


class BinIndexer:

	def __init__(self, arch, component, release, root):
		self.rootdir = os.path.join(root, 'dists', release)
		self.reldir  = os.path.join(component, 'binary-'+arch)

	def create(self, iter):

		def writepkg(pkg, f):
			f.write(pkg['control']
				+ "Filename: "    +  pkg['Filename']
				+ '\nSize: '   + str(pkg['Size'])
				+ '\nMD5Sum: '     + pkg['MD5Sum']
				+ '\nSHA1: '       + pkg['SHA1']
				+ '\nSHA256: '     + pkg['SHA256']
				+ '\nDescription_md5: ' + pkg['Description_md5'] + '\n\n')


		os.makedirs(os.path.join(self.rootdir, self.reldir), exist_ok=True)
		cc = CsumCompressor(
			self.rootdir,
			os.path.join(self.reldir, 'Packages'),
			['none', 'gz', 'xz']
		)
		for pkg in iter: writepkg(pkg, cc)
		result = cc.close()
		print(result)
