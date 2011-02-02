#!/usr/bin/env python

from __future__ import with_statement
from __init__ import version
import os

def main():
	data_dir = os.path.abspath(".")
	base_dir = "/tmp/pynetkey"
	deb_dir = os.path.join(base_dir, "DEBIAN")
	install_dir = os.path.join(base_dir, "usr/share/pyshared/pynetkey")
	try:
		os.makedirs(deb_dir)
	except OSError:
		pass
	try:
		os.makedirs(install_dir)
	except OSError:
		pass

	os.system("hg clone static-http://dip.sun.ac.za/~janto/pynetkey/repo %s" % install_dir)

	control_text = """
Package: pynetkey
Version: %(version)s
Section: web
Priority: optional
Architecture: all
Essential: no
Depends: python-eggtrayicon, python (>=2.6)
Installed-Size: 128
Maintainer: Janto Dreijer <jantod@gmail.com>
Provides: pynetkey
Description: Unofficial GPL alternative to inetkey/sinetkey.
	Its goals are to be more robust and provide some extra functionality.
""" % dict(version=version)
	with file(os.path.join(deb_dir, "control"), "w") as f:
		f.write(control_text)

	with file(os.path.join(deb_dir, "postinst"), "w") as f:
		f.write("#!/bin/sh\n")
	os.chmod(os.path.join(deb_dir, "postinst"), 0755) # make executable

	with file(os.path.join(deb_dir, "prerm"), "w") as f:
		f.write("#!/bin/sh\n")
	os.chmod(os.path.join(deb_dir, "prerm"), 0755) # make executable

	os.system("dpkg --build %s ." % base_dir)

if __name__ == "__main__":
	main()