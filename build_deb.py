#!/usr/bin/env python

"""
this script could probably work as bash script, but I hate bash scripts. http://mywiki.wooledge.org/BashPitfalls
"""

from __future__ import with_statement
from __init__ import version
import os
import shutil
import commands

def write_to_file(filename, text, executable=False):
	with file(filename, "w") as f:
		f.write(text)
	if executable:
		result = commands.getoutput("chmod +x %s" % filename)
		assert not result.strip(), result

def main():
	data_dir = os.path.abspath(".")
	base_dir = "/tmp/pynetkey"
	print "deleting base_dir"
	try:
		shutil.rmtree(base_dir)
	except OSError:
		pass

	print

	print "cloning mercurial repo"
	install_dir = os.path.join(base_dir, "usr/share/pyshared/pynetkey")
	os.makedirs(install_dir)
	os.system("hg clone . %s" % install_dir)
	write_to_file(os.path.join(install_dir, ".hg/hgrc"), """
[paths]
default = static-http://dip.sun.ac.za/~janto/pynetkey/repo
""".lstrip())

	print

	print "creating control files"
	deb_dir = os.path.join(base_dir, "DEBIAN")
	os.makedirs(deb_dir)
	write_to_file(os.path.join(deb_dir, "control"), """
Package: pynetkey
Version: %(version)s
Section: web
Priority: optional
Architecture: all
Essential: no
Depends: python (>=2.6)
Installed-Size: 250
Maintainer: Janto Dreijer <jantod@gmail.com>
Homepage: http://dip.sun.ac.za/~janto/pynetkey
Description: Unofficial GPL alternative to inetkey/sinetkey.
 Pynetkey's primary goals are to be more robust than nxinetkey and to provide some extra functionality and configurability.
""".lstrip() % dict(version=version))

	write_to_file(os.path.join(deb_dir, "postinst"), "#!/bin/sh\napt-key add /usr/share/pyshared/pynetkey/janto.key", executable=1)
	write_to_file(os.path.join(deb_dir, "postrm"), "#!/bin/sh\napt-key del BD3E74C9", executable=1)

	doc_dir = os.path.join(base_dir, "usr/share/doc/pynetkey")
	os.makedirs(doc_dir)

	changelog_filename = os.path.join(doc_dir, "changelog")
	write_to_file(changelog_filename, """
pynetkey (%(version)s) unstable; urgency=low

  * Stuff

 -- Janto Dreijer <jantod@gmail.com>  %(date)s

""".lstrip() % dict(version=version, date=commands.getoutput('date -R')))
	write_to_file(os.path.join(doc_dir, "changelog.Debian"), "see changelog")
	commands.getoutput('gzip -9 %s' % changelog_filename)
	commands.getoutput('gzip -9 %s' % os.path.join(doc_dir, "changelog.Debian"))

	write_to_file(os.path.join(doc_dir, "copyright"), """
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

""".lstrip())

	usr_bin_dir = os.path.join(base_dir, "usr/bin")
	os.makedirs(usr_bin_dir)
	os.system("ln --symbolic /usr/share/pyshared/pynetkey/cli.py %s/pynetkey-cli" % usr_bin_dir)
	#~ os.system("ln --symbolic /usr/share/pyshared/pynetkey/pynetkeyd.sh %s/pynetkey" % usr_bin_dir)

	print

	print "linking icons"
	pixmaps_dir = os.path.join(base_dir, "usr/share/pixmaps")
	os.makedirs(pixmaps_dir)
	for icon_filename in os.listdir(os.path.join(install_dir, "icons")):
		if not icon_filename.endswith(".svg"):
			continue
		if not icon_filename.startswith("pynetkey-"):
			continue
		cmd = "ln --symbolic /usr/share/pyshared/pynetkey/icons/%s %s" % (icon_filename, pixmaps_dir)
		#~ print cmd
		result = commands.getoutput(cmd)
		assert not result.strip(), result

	print

	print "creating menu item"

	shortcut_dir = os.path.join(base_dir, "usr/share/applications")
	os.makedirs(shortcut_dir)
	write_to_file(os.path.join(shortcut_dir, "pynetkey.desktop"), """
[Desktop Entry]
Version=1.0
Name=Pynetkey
Comment=Inetkey in Python
Exec=python /usr/share/pyshared/pynetkey/pynetkey.py
Terminal=false
Type=Application
Icon=/usr/share/pyshared/pynetkey/icons/pynetkey-main.svg
Categories=Network;
""".lstrip())

	print

	print "creating sources.list.d entry"
	sources_list_d = os.path.join(base_dir, "etc/apt/sources.list.d")
	os.makedirs(sources_list_d)
	write_to_file(os.path.join(sources_list_d, "pynetkey.list"), "# Added by pynetkey %s\ndeb http://dip.sun.ac.za/~janto/pynetkey /\n" % version)
	#~ write_to_file(os.path.join(deb_dir, "conffiles"), "sources.list.d/pynetkey.list") #XXX do we actually want to keep sources.list from previous install?

	print

	print "building package"
	print commands.getoutput("fakeroot dpkg --build %s pynetkey%s.deb" % (base_dir, version))

	print

	print "checking package"
	print commands.getoutput("lintian pynetkey%s.deb" % version)

	print

	#~ print "signing package"
	#XXX is default-key respected?
	#~ print commands.getoutput("debsigs --sign=maint --default-key=BD3E74C9 pynetkey%s.deb" % version)

	#~ print

	#~ print "checking signed package"
	#~ print commands.getoutput("lintian pynetkey%s.deb" % version)

	print

	print "building index"
	# http://www.debian.org/doc/manuals/repository-howto/repository-howto.en.html
	print commands.getoutput("dpkg-scanpackages . /dev/null | gzip -9c > Packages.gz")

	print

	print "done"

if __name__ == "__main__":
	main()