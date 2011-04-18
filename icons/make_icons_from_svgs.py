#!/usr/bin/env python

"""
Generates the ICOs that are needed for Windows icons.
I would prefer not to put the generated ICOs under version control as well, but it's less of a pain than having to require windows users to have inkscape (and something to convert from the pngs) installed to build an exe.
"""

import os
for filename in os.listdir("."):
	if not filename.endswith(".svg"):
		continue
	name, _svg = filename.split(".")
	os.system("inkscape --export-png=%s.png -w 128 -h 128 %s" % (name, filename))
	os.system("convert %s.png %s.ico" % (name, name))
	#~ os.remove("%s.png" % name)