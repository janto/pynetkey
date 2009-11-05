from distutils.core import setup
import py2exe
import os
import __init__
from itertools import *

import pynetkey

icon_filenames = ["icons/%s.ico" % c for c in pynetkey.icon_color_mapping.keys()]
icon_indices = [(n, "icons/%s.ico" % c) for c, n in pynetkey.icon_color_mapping.items()]

setup(
	version = __init__.version,
	name = "pynetkey",
	description = "inetkey in system tray",
	zipfile = None, # put in exe

	data_files = [
		("icons", icon_filenames),
		("", ["readme.html"]),
	],

	# targets to build
	windows = [{
		"script": "pynetkey.py",
		"icon_resources": [(1, "icons/main.ico")]+icon_indices, # application icon
	}],
)
