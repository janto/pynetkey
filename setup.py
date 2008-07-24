from distutils.core import setup
import py2exe
import os
import __init__

setup(
	version = __init__.version,
	name = "pynetkey",
	description = "inetkey in system tray",

	data_files = [
		("icons", ["icons/%s" % f for f in os.listdir("icons") if ".svn" not in f]),
		("", ["readme.txt"]),
	],

	# targets to build
	windows = [{
		"script": "pynetkey.py",
		"icon_resources": [(1, "icons/orange.ico")] # application icon
	}],
)
