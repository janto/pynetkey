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

import optparse
import json

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

	@dbus.service.method(dbus_interface=bus_name)
	def stop(self):
		self.inetkey.shutdown()

	@dbus.service.method(dbus_interface=bus_name, out_signature='s')
	def status(self):
		return "open" if self.inetkey.firewall_open else "closed"

	@dbus.service.method(dbus_interface=bus_name, out_signature='s')
	def json_status(self):
		return json.dumps(self.inetkey.status)

	@dbus.service.method(dbus_interface=bus_name, out_signature='s')
	def usage(self):
		return self.inetkey.hint_text[1]

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

pkill_command = 'pkill -9 -f "python.+pynetkey.py"'

def run_client():

	# parse arguments
	parser = optparse.OptionParser(usage="pynetkey [options]")
	parser.add_option("--open", action="store_true", dest="open", default=False, help="open firewall")
	parser.add_option("--close", action="store_true", dest="close", default=False, help="close firewall")

	#~ parser.add_option("--start", action="store_true", dest="start", default=False, help="start a Pynetkey process")
	parser.add_option("--stop", action="store_true", dest="stop", default=False, help="shutdown all Pynetkey processes")
	parser.add_option("--kill", action="store_true", dest="kill", default=False, help="kill all Pynetkey processes (%s)" % pkill_command)

	#~ group = optparse.OptionGroup(parser, "Wait options", "will block until true")
	#~ group.add_option("--wait_until_open", action="store_true", dest="wait_until_open", default=False, help="block until firewall open")
	#~ group.add_option("--wait_until_closed", action="store_true", dest="wait_until_closed", default=False, help="block until firewall closed")
	#~ group.add_option("--wait_until_started", action="store_true", dest="wait_until_started", default=False, help="block until pynetkey started")
	#~ group.add_option("--wait_until_stopped", action="store_true", dest="wait_until_stopped", default=False, help="block until pynetkey stopped")
	#~ parser.add_option_group(group)

	group = optparse.OptionGroup(parser, "Query options", "print status to stdout")
	group.add_option("--pid", action="store_true", dest="pid", default=False, help="print process ID to stdout")
	group.add_option("--json", action="store_true", dest="json_status", default=False, help="print status as returned by firewall to stdout (as json)")
	group.add_option("--status", action="store_true", dest="status", default=False, help="print firewall status to stdout")
	#~ group.add_option("--usage", action="store_true", dest="usage", default=False, help="print current user's usage to stdout")
	group.add_option("--user", action="store_true", dest="user", default=False, help="print current inetkey user to stdout")
	parser.add_option_group(group)

	options, args = parser.parse_args()

	if options.kill:
		os.system(pkill_command)
		return

	bus = dbus.SessionBus()
	try:
		proxy = bus.get_object(bus_name, object_path)
	except dbus.exceptions.DBusException:
		service = None
	else:
		service = dbus.Interface(proxy, bus_name)

	#~ if options.start:
		#~ if service:
			#~ print "pynetkey already started"
			#~ return
		#~ pid = os.fork() #XXX not completely correct
		#~ print "pid", pid
		#~ if pid == 0:
			#~ os.system(r"./pynetkey.py &> \dev\null")
		#~ return

	if not service:
		print("pynetkey not started.")
		parser.print_help()
		return

	if options.stop:
		print("closing firewall and stopping pynetkey process. ctrl-c will kill pynetkey process.")
		try:
			service.stop()
		except KeyboardInterrupt:
			print("keyboard interrupt. running %s" % str(pkill_command))
			os.system(pkill_command)
	#~ elif options.wait_until_started:
		#~ pass
	#~ elif options.wait_until_stopped:
		#~ pass
	#~ elif options.wait_until_open or options.wait_until_closed:
		#~ status_to_wait_for = dict(wait_until_open="open", wait_until_closed="closed")["wait_until_open"]
		#~ interval = 1
		#~ timeout = None # in minutes
		#~ status = None # in seconds
		#~ start_time = time.time()
		#~ while 1:
			#~ status = service.status()
			#~ if status == status_to_wait_for:
				#~ break
			#~ if timeout is not None and timeout*60 < abs(time.time() - start_time): # take abs to handle system time change
				#~ break
			#~ time.sleep(interval)
		#~ print status
	elif options.open:
		service.open()
	elif options.close:
		service.close()
	elif options.pid: # output must be clean to allow usage by other scripts
		print(service.pid())
	elif options.status: # output must be clean to allow usage by other scripts
		print(service.status())
	elif options.json_status: # output must be clean to allow usage by other scripts
		print(service.json_status())
	elif options.user: # output must be clean to allow usage by other scripts
		print(service.user())
	else:
		#~ print "nothing to do"
		parser.print_help()

if __name__ == "__main__":
	run_client()
