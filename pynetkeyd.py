#!/usr/bin/env python

"""

This file is part of Pynetkey.

Pynetkey is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

Pynetkey is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with Pynetkey.  If not, see <http://www.gnu.org/licenses/>.

Copyright 2011 Janto Dreijer <jantod@gmail.com>

"""

import dbus
import dbus.service
import dbus.glib

import os
import sys
import time

bus_name = "za.ac.sun.pynetkey"
object_path = "/za/ac/sun/pynetkey/system"

class DBus_Service(dbus.service.Object):
	def __init__(self, inetkey):
		self.inetkey = inetkey
		_bus_name = dbus.service.BusName(bus_name, bus=dbus.SessionBus())
		dbus.service.Object.__init__(self, _bus_name, object_path)

	@dbus.service.method(dbus_interface=bus_name)
	def open(self):
		self.inetkey.open_firewall()

	@dbus.service.method(dbus_interface=bus_name)
	def close(self):
		self.inetkey.close_firewall()

	@dbus.service.method(dbus_interface=bus_name, out_signature='i')
	def pid(self):
		return os.getpid()

	@dbus.service.method(dbus_interface=bus_name, out_signature='s')
	def status(self):
		return "open" if self.inetkey.firewall_open else "closed"

	#~ @dbus.service.method(dbus_interface=bus_name, out_signature='s')
	#~ def usage(self):
		#~ return "{}"

	@dbus.service.method(dbus_interface=bus_name, out_signature='s')
	def user(self):
		return self.inetkey.username

def service_pid():
	bus = dbus.SessionBus()
	try:
		proxy = bus.get_object(bus_name, object_path)
	except dbus.exceptions.DBusException:
		return None
	service = dbus.Interface(proxy, bus_name)
	return service.pid()

def run_client():
	bus = dbus.SessionBus()
	try:
		proxy = bus.get_object(bus_name, object_path)
	except dbus.exceptions.DBusException:
		print "pynetkey not started"
		return
	service = dbus.Interface(proxy, bus_name)

	if "start" in sys.argv[1:]:
		pass
	elif "stop" in sys.argv[1:]:
		pass
	elif "wait_until_started" in sys.argv[1:]
		pass
	elif ("wait_until_open" in sys.argv[1:]) or ("wait_until_closed" in sys.argv[1:]):
		status_to_wait_for = dict(wait_until_open="open", wait_until_closed="closed")["wait_until_open"]
		interval = 1
		timeout = None # in minutes
		status = None
		start_time = time.time()
		while 1:
			status = service.status()
			if status == status_to_wait_for:
				break
			if timeout is not None and timeout*60 < abs(time.time() - start_time): # take abs to handle system time change
				break
			time.sleep(interval)
		print status
	elif "open" in sys.argv[1:]:
		service.open()
	elif "close" in sys.argv[1:]:
		service.close()
	elif "pid" in sys.argv[1:]:
		print service.pid()
	elif "status" in sys.argv[1:]:
		print service.status()
	elif "user" in sys.argv[1:]:
		print service.user()
	else:
		print "nothing to do"

if __name__ == "__main__":
	run_client()
