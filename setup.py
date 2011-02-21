"""
This file is primarily used by build.bat to create a windows executable.
To install on a Debian system use the deb file. You can create one using build_deb.sh. Or just manually put this directory somewhere permanent and run pynetkey.py.
You could play with "python setup.py sdist" but rather use the build.sh script to package a source distribution.
"""

from distutils.core import setup
import os
import __init__
import platform
from itertools import *
import pynetkey

if platform.system() in ("Windows", "Microsoft"):
	import py2exe

elif platform.system() == "Linux":
	raise Exception(platform.system()+" not supported")

else:
	raise Exception(platform.system()+" not supported")

try:
	icon_filenames = ["icons/%s.ico" % c for c in pynetkey.icon_color_mapping.keys()]
	icon_indices = [(n, "icons/%s.ico" % c) for c, n in pynetkey.icon_color_mapping.items()]
except ImportError:
	print "There is an extra pynetkey directory within this one. Probably left over from another build script. Delete it."
	raise

setup(
	author='Janto Dreijer',
	author_email='jantod@gmail.com',
	description = "GPL inetkey",
	name = "pynetkey",
	url='https://bitbucket.org/janto/pynetkey',
	version = __init__.version,
	zipfile = None, # put in exe

	data_files = [
		("icons", icon_filenames),
		("", ["readme.html"]),
		("", ["license.txt"]),
	],

	# targets to build
	windows = [{
		"script": "pynetkey.py",
		"icon_resources": [(1, "icons/main.ico")]+icon_indices, # application icon
	}],
)