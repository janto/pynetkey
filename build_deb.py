#!/usr/bin/env python

from __future__ import with_statement
from __init__ import version
import os
import shutil

def main():
	data_dir = os.path.abspath(".")
	base_dir = "/tmp/pynetkey"
	shutil.rmtree(base_dir)

	install_dir = os.path.join(base_dir, "usr/share/pyshared/pynetkey")
	try:
		os.makedirs(install_dir)
	except OSError:
		pass
	os.system("hg clone static-http://dip.sun.ac.za/~janto/pynetkey/repo %s" % install_dir)

	shortcut_dir = os.path.join(base_dir, "usr/share/applications")
	try:
		os.makedirs(shortcut_dir)
	except OSError:
		pass
	shortcut_text = """
[Desktop Entry]
Version=1.0
Name=Pynetkey
Comment=Inetkey in Python
Exec=python /usr/share/pyshared/pynetkey/pynetkey.py
Terminal=false
Type=Application
Icon=/usr/share/pyshared/pynetkey/icons/main.png
Categories=Network;
""".lstrip()
	with file(os.path.join(shortcut_dir, "pynetkey.desktop"), "w") as f:
		f.write(shortcut_text)

	deb_dir = os.path.join(base_dir, "DEBIAN")
	try:
		os.makedirs(deb_dir)
	except OSError:
		pass
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
""".lstrip() % dict(version=version)
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