
# Pynetkey

**Note:**
_It's been a long time since I've updated pynetkey. It should still work, but some things below (like the installation instructions) are probably no longer valid. I suggest getting the latest source from [https://github.com/janto/pynetkey](https://github.com/janto/pynetkey) and trying that. Also if you want to open the firewall from the terminal use the `cli.py` file._

This program was _<font color="red">not written by IT</font>_ and is not supported by them!  
Pynetkey's main goals are to be more robust and attractive (it sits in the system tray) than the existing inetkey/sinetkey. It also runs on both Windows and Linux systems. Pynetkey is released under the GPL.

Main site: https://github.com/janto/pynetkey

Bugs and feature requests go here https://github.com/janto/pynetkey/issues

If you need help, email me (Janto Dreijer) at jantod@gmail.com

## Installation

### Windows Installation

1.  download `pynetkey.**zip**` from the main site
2.  extract somewhere permanent and run `pynetkey.exe`
3.  (optional) create a shortcut to `pynetkey.exe` (such as on your desktop)

### Ubuntu Installation

To install the GUI version

1.  download `pynetkey.**deb**` from the main site
2.  open it (by for example double clicking) and click on the "Install Package" button
3.  a Pynetkey icon wil appear in the Applications menu under Internet. You can right click on it to add an additional launcher icon to the desktop.
4.  an entry under `sources.list.d` will be automatically added

The GUI version was developed with an ubuntu/gnome system in mind. A minimal single-file non-gui version is also available as `cli.py` and should run on most systems with Python2.6. If you have an earlier Python, installing the [SSL package](http://pypi.python.org/pypi/ssl/) might work. If you installed the GUI version, the non-gui version is accessible from the terminal as `python-cli`.

## Licensing

Pynetkey is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.

Pynetkey is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the [GNU General Public License](http://www.gnu.org/licenses/gpl.html) for more details.

## Development

Since the code is GPL, feel free to start hacking at it. If you do something interesting let me know and I might integrate it with my version. You can pull the latest code from the main repository with
*    `git clone git@github.com:janto/pynetkey.git`

For this to work you need to be already connected to the internet

### Windows Build requirements

You can run `build.bat` to create a distribution file. You will need:
*   at least python2.6
*   py2exe
*   pywin32

## Config File

### Location

Pynetkey's default behaviour can be modified by creating a config file in the following location (or just select "Edit config file..." from the popup menu):

*   On Windows: `~\inetkey.ini` (usually `C:\Documents and Settings\username\inetkey.ini`)
*   On Linux: `~/.inetkeyrc`

### Saving your username and password

_<font color="red">WARNING:</font>_ Please be aware how dangerous it is to store your username and password on your computer. If you don't know why this is dangerous, I suggest you rather not do it. Someone can easily steal your password. This is also why I won't make this feature easily available from the GUI. IT does not like the idea of people storing their passwords on disk.

Pynetkey will automatically encode the password to prevent wandering eyes from stealing your password, but it is _<font color="red">NOT</font>_ the same as it being encrypted.

### Scheduling

You can force an open or close event at scheduled times. This is useful for things like automated downloads / torrenting. The current implementation is accurate to within 30 seconds.

The events in the example config file might also be useful. It will open the firewall 5 minutes before the low cost timeslot and closes it 5 minutes before it ends.

Remember that the amount you get charged depends on the timeslot in which your download finishes. Also, configure your download manager / torrent application to stop in time. Don't trust that your download will stop just because you closed the firewall.

Under the `[events]` section you need to have entries in the form of `close1 = Mon 07:55`. The day of week is optional, so `open3 = 02:00` will open the firewall each morning at 2 am.

### Other Settings

Setting `open_on_launch=1` (the default) will open the firewall on pynetkey's launch. Set `open_on_launch=0` to disable this feature.

Setting `notify_on_error=1` (default) will use pynotify to alert the user when an error occurs. This might become irritating on bad connections (SCN/matieswifi), in which case disable it by setting it equal to `0`.

### Config Example

	[config]
	username = 12345678
	password = supersecret
	open_on_launch = 1
	notify_on_error = 1

	[events]

	close1 = Mon 07:55
	open1 = Mon 23:55

	close2 = Tue 07:55
	open2 = Tue 23:55

	close3 = Wed 07:55
	open3 = Wed 23:55

	close4 = Thu 07:55
	open4 = Thu 23:55

	close5 = Fri 07:55
	open5 = Fri 23:55

## Tips and Tricks

The deb file installs a shortlink to `cli.py` as `/usr/bin/pynetkey-cli`. That means you can just type `pynetkey-cli` into the terminal for quick firewall control.

The `pynetkey` terminal command will give you some control of a running pynetkey gui process.

If you want a more persistent command line process you might be interested in the following command: `screen -d -m pynetkey-cli -c ~/.inetkeyrc` This will create a screen session and immediatly detach it. `cli.py` will continue to log in and stay connected. You will need to attach the screen with `screen -r` to log out when you're done.
