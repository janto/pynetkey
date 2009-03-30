This program is not supported by IT!

contact
=======
- jantod@gmail.com

download
========

Windows build is downloadable here: http://dip.sun.ac.za/~janto/
The source code is currently hosted on assembla.com. Subversion checkout: http://svn.assembla.com/svn/pynetkey

windows build requirements
==========================
- python2.5
- py2exe
- pywin32 (210 works. popup menu icons disappeared for 211,212,213)

Run build.bat to create distribution.

installation (Windows)
======================
1) extract somewhere and run pynetkey.exe

installation (Debian)
=====================

1) sudo apt-get install python-gtk2 python-gnome2-extras
2) (optional) create shortcut to pynetkey.py (use ''icons/main.ico'' for icon)
3) (optional) create config file to save settings. See blelow.

settings
========

To avoid prompting for username/password every time you can place it in a config file.
WARNING: Please be aware how dangerous this is. If you don't know why this is dangerous, I suggest you rather not do it. Someone can easily steal your password.

On Windows: ~\inetkey.ini (i.e. "C:\Documents and Settings\username\inetkey.ini")
On Linux: ~/.inetkeyrc

You can also force open and close events at scheduled times. Useful for things like late night downloads / torrents. Current implementation is accurate to within 30seconds. Will fix when I have time.

Example::

	[config]
	username=12345678
	password=supersecret

	[events]
	open = 02:05
	close = 07:55


The password will automatically be encoded (not encrypted) to prevent wandering eyes from stealing your password.

todo
===
port to wx (easier to manage cross platform)
links
	help file

