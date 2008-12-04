This program is not supported by IT!
jantod@gmail.com

contact
=====
- jantod@gmail.com

windows build requirements
=================
- python2.5
- py2exe
- pywin32

Run build.bat to create distribution.

installation (Windows)
==============
1) extract somewhere and run pynetkey.exe

installation (Debian)
=============

1) sudo apt-get install python-gtk2 python-gnome2-extras
2) (optional) create shortcut to pynetkey.py (use ''icons/main.ico'' for icon)
3) (optional) create config file to save settings. See blelow.

settings
=====

To avoid prompting for username/password every time you can place it in a config file.

On Windows: ~\inetkey.ini (i.e. "C:\Documents and Settings\username\inetkey.ini")
On Linux: ~/.inetkeyrc

You can also force open and close events at scheduled times. Current implementation is accurate to within 30seconds. Will fix when I have time.

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
calculate optimal reconnection delay
