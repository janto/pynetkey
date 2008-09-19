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

installation (Debian)
=============

1) sudo apt-get install python-gtk2 python-gnome2-extras
2) (optional) create shortcut to pynetkey.py (use ''icons/main.ico'' for icon)
3) (optional) create config file to save settings. See blelow.

settings
=====

To avoid prompting for username/password you can place it in a config file:

On Windows: ~\inetkey.ini (e.g. "C:\Documents and Settings\username\inetkey.ini")
One Linux: ~/.inetkeyrc

[config]
username=12345678
password=supersecret
