#!/usr/bin/env python

from __future__ import with_statement
from __init__ import version
import os
import shutil

def main():
	data_dir = os.path.abspath(".")
	base_dir = "/tmp/pynetkey"
	print "deleting base_dir"
	try:
		shutil.rmtree(base_dir)
	except OSError:
		pass

	print "pulling from dip.sun.ac.za"
	install_dir = os.path.join(base_dir, "usr/share/pyshared/pynetkey")
	try:
		os.makedirs(install_dir)
	except OSError:
		pass
	os.system("hg clone static-http://dip.sun.ac.za/~janto/pynetkey/repo %s" % install_dir)

	print "creating files."
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
Depends: python (>=2.6)
Installed-Size: 150
Maintainer: Janto Dreijer <jantod@gmail.com>
Provides: pynetkey
Description: Unofficial GPL alternative to inetkey/sinetkey.
	Its goals are to be more robust and provide some extra functionality.
""".lstrip() % dict(version=version)
	with file(os.path.join(deb_dir, "control"), "w") as f:
		f.write(control_text)

	copyright_text = """
Upstream Author(s):

    Janto Dreijer <jantod@gmail.com>

Copyright:

    Copyright (C) 2011 Janto Dreijer

License:

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This package is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.

On Debian systems, the complete text of the GNU General
Public License version 3 can be found in `/usr/share/common-licenses/GPL-3'.

""".lstrip()
	with file(os.path.join(deb_dir, "copyright"), "w") as f:
		f.write(copyright_text)

	with file(os.path.join(deb_dir, "postinst"), "w") as f:
		f.write("""
#!/bin/sh
ln --symbolic /usr/share/pyshared/pynetkey/cli.py /usr/bin/pynetkey-cli
""".lstrip())
	os.chmod(os.path.join(deb_dir, "postinst"), 0755) # make executable

	with file(os.path.join(deb_dir, "prerm"), "w") as f:
				f.write("""
#!/bin/sh
rm /usr/bin/pynetkey-cli
""".lstrip())
	os.chmod(os.path.join(deb_dir, "prerm"), 0755) # make executable

	print "building package"
	os.system("dpkg --build %s pynetkey.deb" % base_dir)

	print "done"

if __name__ == "__main__":
	main()