#!/usr/bin/env python3
'''
Create an index file from an iterator that yields packages
'''

import datetime, os, os.path, subprocess
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
			result.append((fname, hash.digest()))
		return result


class BinIndexer:

	def __init__(self, arch, component, release, root):
		self.rootdir = os.path.join(root, 'dists', release)
		self.reldir  = os.path.join(component, 'binary-'+arch)

	def create(self, iter):
		'''
		Create the index files and return a list

		Each list entry is a tuple with filename and its hashes
		'''

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
		return cc.close()

def _updateRelease(release, db, root):
	'''
	Update the (changed) indices then create and sign the Release file
	'''
	csums = dict(MD5Sum=[], SHA1=[], SHA256=[])
	for comp in release.components:
		for arch in release.architectures:
			isum = BinIndexer(arch, comp, release.name, root).create(
				db.getIndex(arch, comp, release.id)
			)

			for file,hashes in isum:
				for hash in ('MD5Sum', 'SHA1', 'SHA256'):
					csums[hash].append((
						getattr(hashes,hash),
						hashes.Size,
						file
					))
	# indices are written, compressed and checksums computed
	# now print result to release file
	with open(os.path.join(root, 'dists', release.name, 'Release'), 'w') as f:
		for label in ('description', 'origin', 'label', 'version', 'suite'):
			if not hasattr(release, label): continue
			val = getattr(release, label)
			if val != None:
				f.write(label.capitalize() + ': '+ val + '\n')
		f.write('Codename: '+ release.name + '\n')
		f.write('Architectures: ' + ' '.join(release.architectures) + '\n')
		f.write('Components: ' + ' '.join(release.components) + '\n')
		d = datetime.datetime.utcnow().strftime('%a, %d %b %Y %H:%M:%S +0000')
		f.write('Date: ' + d + '\n')
		for hash in ('MD5Sum', 'SHA1', 'SHA256'):
			f.write(hash + ':\n')
			# sort list of (hexsum, size, filename) by the latter
			csums[hash].sort(key=lambda x: x[2])
			for hashval, size, fname in csums[hash]:
				f.write(' ' + hashval + ' ' + size.rjust(9) + ' ' + fname + '\n')

def _signRelease(release, root, key):
	gpgargs = ['gpg', '--no-tty', '--batch' ]
	if key != None:
		gpgargs += [ '--local-user', key ]
	relfile = os.path.join(root, 'dists', release.name, 'Release')
	inlfile = os.path.join(root, 'dists', release.name, 'InRelease')
	sigfile = relfile + '.gpg'
	os.remove(sigfile)
	res = subprocess.run(gpgargs + [
		'--detach-sign', '-o', sigfile, relfile
	])
	os.remove(inlfile)
	res = subprocess.run(gpgargs + [
		'--clearsign', '-o', inlfile, relfile
	])

def updateRelease(release, db, config):
	_updateRelease(release, db, config.root)
	_signRelease(release, config.root, release.gpgkey)
