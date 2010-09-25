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

Copyright 2009 Janto Dreijer <jantod@gmail.com>

"""

from __future__ import division, with_statement

refresh_frequency = 6*60
usage_query_frequency = 1*60
check_schedule_frequency = 30 # must be faster than every 60sec to avoid missing a minute
default_connection_hostname = "fw.sun.ac.za"
connection_port = 950
connection_timeout = 15
connection_retries = 3

import locale
locale.setlocale(locale.LC_ALL, 'C') # necessary for scheduler to match days of week consistently

import ssl
import socket
socket.setdefaulttimeout(connection_timeout) # global timeout
import urllib2, urllib

import re
from threading import Thread, Timer, Event

from time import localtime, strftime, sleep

import os
import os.path
import platform
import sys
import traceback

import __init__
version = "pynetkey %s" % __init__.version

import logging
logger = logging.getLogger("")
logging.basicConfig(format="%(levelname)s@%(asctime)s=%(name)s:%(message)s", datefmt="%Y-%m-%d %H:%M")
logging.root.setLevel(logging.WARN)
if os.path.exists("debug_flag_file"):
	logging.root.setLevel(logging.DEBUG)

# determine root directory
root_dir = os.path.abspath(sys.path[0]) # can't use __file__ with py2exe
if os.path.isfile(root_dir): # py2exe gives library.zip as path[0]
	root_dir = os.path.dirname(root_dir)
assert os.path.exists(os.path.join(root_dir, "icons")), root_dir

# load platform specific gui code

if platform.system() in ("Windows", "Microsoft"):
	from systrayicon import password_dialog, TrayIcon, gui_quit
	#~ from wxtrayicon import TrayIcon, password_dialog, gui_quit
	import win32api
	def open_url(url):
		win32api.ShellExecute(0,None,url,None,None,1)
	def workstation_is_locked():
		user32 = ctypes.windll.User32
		OpenDesktop = user32.OpenDesktopA
		SwitchDesktop = user32.SwitchDesktop
		DESKTOP_SWITCHDESKTOP = 0x0100
		hDesktop = OpenDesktop("default", 0, False, DESKTOP_SWITCHDESKTOP)
		result = SwitchDesktop(hDesktop)
		return not result # no active desktop
	config_filename = os.path.join(os.environ['HOMEDRIVE'], os.environ['HOMEPATH'], "inetkey.ini") # HOME is unreliable
	TEMP_DIRECTORY = os.environ['TEMP'] or os.environ['TMP']

#~ elif platform.system() == "Linux": #XXX and mac?
	#~ from wxtrayicon import TrayIcon, password_dialog, gui_quit
	#~ def open_url(url):
		#~ os.system('gnome-open %s' % url)
	#~ def workstation_is_locked():
		#~ return False
	#~ config_filename = os.path.expanduser("~/.inetkeyrc")
	#~ TEMP_DIRECTORY = "/tmp"

elif platform.system() == "Linux":
	from gtktrayicon import password_dialog
	from gtktrayicon import GtkTrayIcon as TrayIcon
	from gtk import main_quit as gui_quit
	def open_url(url):
		os.system('xdg-open %s' % url)
	def workstation_is_locked():
		return False
	config_filename = os.path.expanduser("~/.inetkeyrc")
	TEMP_DIRECTORY = "/tmp"

else:
	raise Exception(platform.system()+" not supported")

# set up paths
assert os.path.exists(TEMP_DIRECTORY), TEMP_DIRECTORY
log_filename = os.path.join(TEMP_DIRECTORY, "pynetkey_error.txt")

class ReTimer(Thread):

	def __init__(self, interval, function, args=[], kwargs={}, immediate=False):
		Thread.__init__(self)
		self.immediate = immediate
		self.interval = interval
		self.function = function
		self.args = args
		self.kwargs = kwargs
		self.finished = Event()

	#~ def start(self):
		#~ Thread.start(self)

	def stop(self):
		self.finished.set()

	def run(self):
		if self.immediate:
			self.function(*self.args, **self.kwargs)
		while 1:
			self.finished.wait(self.interval) # wait for delay or kill signal
			if self.finished.isSet(): # kill signal
				return
			self.function(*self.args, **self.kwargs)

class ConnectionException(Exception):
	pass

# icon positions in compiled exe
icon_color_mapping = dict(blue=101, green=102, orange=103, red=104, yellow=105)

def get_icon(name):
	filename = os.path.abspath(os.path.join(root_dir, "icons/%s.ico" % name))
	if os.path.exists(filename):
		return filename
	return icon_color_mapping[name] # try icon in exe

import ConfigParser
import base64
import stat
_cached_config = None
def get_config_file():
	"""Translate conf file into dict"""

	global _cached_config
	if _cached_config is not None:
		return _cached_config

	logger.debug("reading config from %s" % config_filename)

	if not os.path.exists(config_filename):
		# create empty config file
		file(config_filename, "w")

	# make file user-level read/write only
	os.chmod(config_filename, stat.S_IRUSR | stat.S_IWUSR)

	# load password and save encoded back to config file
	conf_obj = ConfigParser.ConfigParser()
	conf_obj.add_section("config")
	conf_obj.set("config", "password", "")
	conf_obj.set("config", "encoded_password_b32", "")
	conf_obj.read(config_filename)
	password = conf_obj.get("config", "password")
	if password: # provided as plaintext
		logger.debug("encoding password and saving into %s" % config_filename)
		encoded_password = base64.b32encode(password)
		conf_obj.set("config", "encoded_password_b32", encoded_password)
		conf_obj.set("config", "password", "") # clear plaintext
		# save encoded password
		with file(config_filename, "w") as f:
			conf_obj.write(f)
	del conf_obj # just to emphasize independance from rest of code
	del password # just to emphasize independance from rest of code

	# set default values
	conf_obj = ConfigParser.ConfigParser()
	conf_obj.add_section("config")
	conf_obj.set("config", "username", "")
	conf_obj.set("config", "password", "")
	conf_obj.set("config", "encoded_password_b32", "")
	conf_obj.set("config", "open_on_launch", "1")
	conf_obj.set("config", "connection_hostname", default_connection_hostname)
	conf_obj.add_section("events")

	# read settings
	conf_obj.read(config_filename)
	config = dict()
	config["username"] = conf_obj.get("config", "username")
	config["open_on_launch"] = conf_obj.get("config", "open_on_launch") == "1"
	config["connection_hostname"] = conf_obj.get("config", "connection_hostname")

	# handle password
	config["password"] = conf_obj.get("config", "password")
	config["encoded_password_b32"] = conf_obj.get("config", "encoded_password_b32")
	if config["password"]: # password provided as plaintext
		assert False, "password should have been encoded"
	elif config["encoded_password_b32"]: # password was encoded
		logger.debug("decoding password")
		config["password"] = base64.b32decode(config["encoded_password_b32"])
	else: # no password provided
		logger.debug("no password provided in config file")
		pass

	# handle scheduled open / close events
	config["open_times"] = []
	config["close_times"] = []
	for name, t in sorted(conf_obj.items("events")):
		t = t.lower() # try to be lenient
		if name.startswith("open"):
			config["open_times"].append(t)
			continue
		if name.startswith("close"):
			config["close_times"].append(t)
			continue
	logger.debug("open times: %s" % config["open_times"])
	logger.debug("close times: %s" % config["close_times"])

	_cached_config = config
	return config

def prompt_username_password(force_prompt=False):
	if not force_prompt:
		config = get_config_file()
		if config["username"] and config["password"]:
			return config["username"], config["password"]
	return password_dialog()

def get_usage(username, password):
	url = "https://maties2.sun.ac.za/fwusage/"

	class FancyURLopener(urllib.FancyURLopener):
		def prompt_user_passwd(self, a, b):
			return username, password

	opener = FancyURLopener(proxies={}) # no proxy
	try:
		result = opener.open(url, data=urllib.urlencode([("client", version)])) # maybe IT will one day want to block a specific version?
	except RuntimeError: #maximum recursion depth exceeded
		#XXX why this sometimes happens is beyond me
		return None
	data = result.read()

	result = re.findall('<td align="right"><font size="1">(.*)</font></td>', data)
	if result:
		return result[-1], result[-2]
	return None

class Inetkey(object):

	def __init__(self, username, password):

		config = get_config_file()

		self.logger = logging.getLogger("Inetkey")
		self.connection_hostname = config["connection_hostname"]
		self.username = username
		self.password = password
		self.open_on_launch = config["open_on_launch"]
		self.firewall_open = False
		self.close_on_workstation_locked = False

		def refresh():
			if self.firewall_open:
				if self.close_on_workstation_locked:
					while workstation_is_locked():
						self.close_firewall()
						sleep(5) # frequency to check if workstation unlocked
				self.logger.debug("refreshing connection")
				self.open_firewall()
		self.refresher = ReTimer(refresh_frequency, refresh)

		def check_usage():
			if not self.firewall_open:
				return
			self.logger.debug("querying usage")
			try:
				usage = get_usage(self.username, self.password)
				self.logger.debug("usage query result: %s" % `usage`)
				if usage is not None:
					self.systrayicon.set_hover_text("R%s = %s MB" % usage)
			except Exception, e:
				#~ raise
				self.systrayicon.set_hover_text("error checking usage: "+str(e))
		self.usage_checker = ReTimer(usage_query_frequency, check_usage, immediate=True)

		# scheduler
		#XXX hackish approach to schedule events
		def check_schedule(_prev_check_time=["never"]):
			time_as_text = strftime("%H:%M")
			date_as_text = strftime("%a %H:%M").lower()
			if _prev_check_time[0] == time_as_text:
				return # already checked in this minute
			self.logger.debug("checking for scheduled open or close (%s, %s)" % (time_as_text, date_as_text))

			if time_as_text in config["open_times"] or date_as_text in config["open_times"]:
				self.logger.info("opening as per schedule")
				self.open_firewall()

			if time_as_text in config["close_times"] or date_as_text in config["close_times"]:
				self.logger.info("closing as per schedule")
				self.close_firewall()

			_prev_check_time[0] = time_as_text

		self.retimer_check_schedule = ReTimer(check_schedule_frequency, check_schedule, immediate=True)

		self.systrayicon = TrayIcon()

# ---------------
# app logic

	def startup(self, systrayicon):
		self.systrayicon = systrayicon
		self.set_connected_status(False)
		if self.open_on_launch:
			self.open_firewall()
		self.refresher.start()
		self.usage_checker.start()
		self.retimer_check_schedule.start()

	def shutdown(self):
		self.refresher.stop()
		self.usage_checker.stop()
		self.retimer_check_schedule.stop()
		self.close_firewall()

	def run(self):
		# create system tray menu
		def toggle_connection_state(event):
			if self.firewall_open:
				self.close_firewall()
			else:
				self.open_firewall()
		def on_quit(hwnd=0, msg=0, wparam=0, lparam=0):
			try:
				self.shutdown()
			finally:
				gui_quit()
				return 1
		def change_user(event):
			username, password = prompt_username_password(force_prompt=True)
			if username and password:
				self.close_firewall()
				self.username, self.password = username, password
				self.open_firewall()
		def toggle_close_on_workstation_locked(sysTrayIcon):
			self.close_on_workstation_locked = not self.close_on_workstation_locked
			#~ self.logger.info("close_on_workstation_locked=%s" % self.close_on_workstation_locked)
			#~ print "close_on_workstation_locked=%s" % self.close_on_workstation_locked

		menu_options = []
		menu_options.append(("Toggle FireWall", None, toggle_connection_state))
		menu_options.append(("Open FireWall", get_icon("green"), lambda e: self.open_firewall()))
		menu_options.append(("Close FireWall", get_icon("orange"), lambda e: self.close_firewall()))
		menu_options.append(("-", None, None))
		if platform.system() in ("Windows", "Microsoft"):
			menu_options.append(("Close on Workstation Lock", lambda: self.close_on_workstation_locked, toggle_close_on_workstation_locked))
		menu_options.append(("Change user...", None, change_user))
		menu_options.append(("Edit config file...", None, lambda e: open_url(config_filename)))
		menu_options.append(("-", None, None))
		menu_options.append(("User admin page...", None, lambda e: open_url('http://www.sun.ac.za/useradm')))
		menu_options.append(("Firewall usage...", None, lambda e: open_url('https://maties2.sun.ac.za/fwusage/')))
		menu_options.append(("IT website...", None, lambda e: open_url('http://it.sun.ac.za/')))
		menu_options.append(("-", None, None))
		self.systrayicon.construct(menu_options, startup=self.startup, on_quit=lambda e: on_quit())

# ---------------
# networking

	def make_request(self, variables=[]):
		e = "error connecting"
		for retry in range(connection_retries): #XXX technically unused
			# python's urllib sucks. easier to do things directly with sockets
			s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
			ssl_sock = ssl.wrap_socket(s,
				#~ ca_certs="/etc/ca_certs_file",
				cert_reqs=ssl.CERT_NONE,
				#~ cert_reqs=ssl.CERT_REQUIRED,
				#~ ssl_version=ssl.PROTOCOL_SSLv3,
				ssl_version=ssl.PROTOCOL_TLSv1,
			)
			ssl_sock.connect((self.connection_hostname, connection_port))

			#~ print repr(ssl_sock.getpeername())
			#~ print ssl_sock.cipher()
			#~ print pprint.pformat(ssl_sock.getpeercert())

			encoded_variables = urllib.urlencode(variables)
			request = "\r\n".join([
				"POST / HTTP/1.1" if variables else "GET / HTTP/1.1",
				"Host: %s" % self.connection_hostname,
				"User-Agent: %s" % version,
				"Content-Length: %d" % len(encoded_variables),
				"Referer: https://%s:%d/" % (self.connection_hostname, connection_port),
				"",
				encoded_variables,
			])
			#~ print request
			#~ print
			ssl_sock.write(request)

			# Read a chunk of data.  Will not necessarily read all the data returned by the server.
			response = ssl_sock.read()
			#~ print response

			# note that closing the SSLSocket will also close the underlying socket
			ssl_sock.close()

			# break from retry loop
			return response
		raise ConnectionException(str(e))

	def authenticate(self):
		# get sesion ID
		logger.debug("connecting")
		try:
			response = self.make_request()
		except (ssl.SSLError, socket.error), e:
			raise ConnectionException(e)
		session_id = re.findall('<input type="hidden" name="ID" value="(.*)"', response)[0]
		# send username
		self.logger.debug("sending username")
		assert "user" in response.lower(), response
		response = self.make_request([('ID', session_id), ('STATE', "1"), ('DATA', self.username)])
		# send password
		self.logger.debug("sending password")
		assert "password" in response.lower(), response
		response = self.make_request([('ID', session_id), ('STATE', "2"), ('DATA', self.password)])
		stripped_response = re.findall('<font face="verdana" size="3">(.*)', response)[0].strip()
		if "denied" in response:
			raise ConnectionException(stripped_response)
		else:
			self.logger.info(stripped_response)
		return session_id

	def open_firewall(self):
		self.info("opening firewall...")
		try:
			session_id = self.authenticate()
			# open request
			self.logger.debug("sending 'sign-on' request")
			self.make_request([('ID', session_id), ('STATE', "3"), ('DATA', "1")])
			self.set_connected_status(connected=True)
		except ConnectionException, e:
			self.error(str(e))
			#~ raise

	def close_firewall(self):
		if not self.firewall_open:
			return
		self.info("closing firewall...")
		try:
			session_id = self.authenticate()
			# close request
			self.logger.debug("sending 'sign-off' request")
			self.make_request([('ID', session_id), ('STATE', "3"), ('DATA', "2")])
			self.set_connected_status(connected=False)
		except ConnectionException, e:
			self.error(str(e))

# ---------------
# display

	def set_connected_status(self, connected=True):
		self.firewall_open = connected # set state
		if connected:
			self.logger.debug("opened")
			self.systrayicon.set_icon(get_icon("green"), "connection open")
		else:
			self.logger.debug("closed")
			self.systrayicon.set_icon(get_icon("orange"), "connection closed")

	def error(self, text):
		self.logger.error(text)
		self.systrayicon.set_icon(get_icon("red"), text)

	def warn(self, text):
		self.logger.debug(text)
		self.systrayicon.set_icon(get_icon("red"), text)

	def info(self, text):
		self.logger.info(text)
		self.systrayicon.set_icon(get_icon("yellow"), text)

def main():
	# get password and username
	username, password = prompt_username_password()
	if username and password:
		# create application
		inetkey = Inetkey(username, password)
		inetkey.run()
		sys.exit() # makes sure everything is dead. get_usage() might take loooong to timeout.

if __name__ == '__main__':
	try:
		main()
	except SystemExit:
		pass
	except: # log any unexpected exceptions
		traceback.print_exc(file=file(log_filename, "w"))
		raise
