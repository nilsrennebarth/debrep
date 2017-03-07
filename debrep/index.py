#!/usr/bin/env python3
'''
Create an index file from an iterator that yields package ids
'''

import os, os.path

class BinIndexer:

	def __init__(self, arch, component, release, root):
		self.dir = os.path.join(root, 'dists', release, component,
			'binary-'+arch)

	def create(self, iter):

		def writepkg(pkg, f):
			f.write(pkg['control'] +
			"Filename: {Filename}\n"
			"Size: {Size!s}\n"
			"MD5Sum: {MD5Sum}\n"
			"SHA1: {SHA1}\n"
			"SHA256: {SHA256}\n"
			"Description_md5: {Description_md5}\n\n".format(**pkg))

		os.makedirs(self.dir, exist_ok=True)
		with open(os.path.join(self.dir, 'Packages'), "w") as f:
			for pkg in iter: writepkg(pkg, f)
