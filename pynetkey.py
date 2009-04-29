#!/usr/bin/env python

"""Inetkey in Python.

	Janto Dreijer <jantod@gmail.com>

"""

from __future__ import division, with_statement

refresh_frequency = 6*60
usage_query_frequency = 1*60
check_schedule_frequency = 30 # must be faster than every 60sec to avoid missing a minute
connection_url = "https://fw.sun.ac.za:950"
connection_timeout = 15
connection_retries = 3

import logging
logger = logging.getLogger("")
logging.root.setLevel(logging.WARN)
#~ logging.root.setLevel(logging.DEBUG)
logging.basicConfig(format="%(levelname)s@%(asctime)s=%(name)s:%(message)s", datefmt="%Y-%m-%d %H:%M")

import traceback

import socket
socket.setdefaulttimeout(connection_timeout) # global timeout
import urllib2, urllib

import re
import signal
from threading import Thread, Timer, Event
from time import localtime, strftime, sleep
from datetime import timedelta, datetime
import os
import platform

import sys
import os.path

import time

import __init__
version = "pynetkey %s" % __init__.version

# determine root directory
root_dir = os.path.abspath(sys.path[0]) # can't use __file__ with py2exe
if os.path.isfile(root_dir): # py2exe gives library.zip as path[0]
	root_dir = os.path.dirname(root_dir)
assert os.path.exists(os.path.join(root_dir, "icons")), root_dir

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
		os.system('gnome-open %s' % url)
	def workstation_is_locked():
		return False
	config_filename = os.path.expanduser("~/.inetkeyrc")
	TEMP_DIRECTORY = "/tmp"

else:
	raise Exception(platform.system()+" not supported")

logger.debug("using config_filename %s" % config_filename)

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
def prompt_username_password(force_prompt=False):
	if not force_prompt:
		logger.debug("reading from %s" % config_filename)

		if not os.path.exists(config_filename):
			# create empty config file
			file(config_filename, "w")

		# make file user-level read/write only
		os.chmod(config_filename, stat.S_IRUSR | stat.S_IWUSR)

		# process config file
		config = ConfigParser.ConfigParser()
		config.read(config_filename)
		try:
			username = config.get("config", "username")
			password = config.get("config", "password")
		except ConfigParser.NoSectionError:
			pass # ignore config file
		else:
			if password: # provided as plaintext
				encoded_password = base64.b32encode(password)
				config.set("config", "encoded_password_b32", encoded_password)
				config.set("config", "password", "") # clear plaintext
				# save encoded password
				with file(config_filename, "w") as f:
					config.write(f)

			else:
				encoded_password = config.get("config", "encoded_password_b32")
				password = base64.b32decode(encoded_password)

			return username, password
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
		return result[-1]
	return None

class Statistics(object):

	def __init__(self):
		self.open_events = []
		self.events = []

	def firewall_open(self):
		self.open_events.append(localtime())
		self.events.append((localtime(), "open"))

	def firewall_closed(self):
		self.events.append((localtime(), "close"))

	def firewall_error(self, text):
		self.events.append((localtime(), "error", text))

	def __str__(self):
		d = {}
		if self.open_events:
			d["first opened"] = strftime("%a, %d %b %Y %H:%M:%S", self.open_events[0])
			d["last opened"] = strftime("%a, %d %b %Y %H:%M:%S", self.open_events[-1])
			firewall_open = timedelta(seconds=refresh_frequency) * len(self.open_events)
			d["time firewall open"] = firewall_open
			pynetkey_open = datetime(*localtime()[:-2]) - datetime(*self.open_events[0][:-2])
			d["time pynetkey open"] = pynetkey_open
			d["connected"] = firewall_open.seconds / pynetkey_open.seconds
			d["refreshes"] = len(self.open_events)
		return "{%s}" % ", ".join("'%s':'%s'" % (k, str(v)) for k, v in d.items())

	def dump_to_file(self):
		with file(os.path.join(root_dir, "stats.log"), "a+") as f:
			f.write("%s\n" % self)
			for event in self.events:
				f.write("%s\n" % event)

class Inetkey(object):

	def __init__(self, username, password, open_on_launch=True):
		self.logger = logging.getLogger("Inetkey")
		self.statistics = Statistics()
		self.url = connection_url
		self.username = username
		self.password = password
		self.open_on_launch = open_on_launch
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
			self.logger.debug("querying usage")
			try:
				usage = get_usage(self.username, self.password)
				self.logger.debug("usage query result: %s" % usage)
				if usage:
					self.systrayicon.set_hover_text("R%s" % usage)
			except Exception, e:
				#~ raise
				self.systrayicon.set_hover_text("error checking usage: "+str(e))
		self.usage_checker = ReTimer(usage_query_frequency, check_usage, immediate=True)

		# scheduler
		#XXX hackish approach to schedule events
		open_time = None
		close_time = None
		if os.path.exists(config_filename):
			config = ConfigParser.ConfigParser()
			config.read(config_filename)
			try:
				open_time = config.get("events", "open", "")
				close_time = config.get("events", "close", "")
			except (ConfigParser.NoSectionError, ConfigParser.NoOptionError):
				pass
		def check_schedule(_prev_check_time=[""]):
			time_as_text = time.strftime("%H:%M")
			if _prev_check_time[0] == time_as_text:
				return # already checked in this minute
			self.logger.debug("checking for scheduled open or close")

			if time_as_text == open_time:
				self.logger.info("opening as per schedule")
				self.open_firewall()

			if time_as_text == close_time:
				self.logger.info("closing as per schedule")
				self.close_firewall()

			_prev_check_time[0] = time_as_text

		self.retimer_check_schedule = ReTimer(check_schedule_frequency, check_schedule, immediate=True)

		self.systrayicon = TrayIcon()

# ---------------
# app logic

	def startup(self, systrayicon):
		self.systrayicon = systrayicon
		self.connected(False)
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
		self.statistics.dump_to_file()

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
		menu_options.append(("Tariff structure...", None, lambda e: open_url('http://infoteg.sun.ac.za/infoteg/IN_Tariewe_E.htm')))
		menu_options.append(("-", None, None))
		self.systrayicon.construct(menu_options, startup=self.startup, on_quit=lambda e: on_quit())

# ---------------
# networking

	def make_request(self, variables=[]):
		e = "error connecting"
		for retry in range(connection_retries):
			try:
				if variables:
					variables.insert(0, ("client", version)) # maybe IT will one day want to block a specific version?
					request = urllib2.Request(url=self.url, data=urllib.urlencode(variables))
				else:
					request = urllib2.Request(url=self.url)
				request.timeout = connection_timeout #XXX hack to make it work with python2.6
				#~ self.logger.debug(request.get_data())
				response = urllib2.HTTPSHandler().https_open(request).read()
			except urllib2.URLError, e:
				self.logger.debug("attempt %d failed: %s" % (retry, str(e)))
				continue # try again
			except Exception, e:
				#~ raise
				raise ConnectionException(str(e))
			if not response:
				raise ConnectionException("no response from server")
			assert "ERROR" not in response, response

			# break from retry loop
			return response
		raise ConnectionException(str(e))

	def authenticate(self):
		# get sesion ID
		self.logger.debug("connecting")
		response = self.make_request()
		session_id = re.findall('<INPUT TYPE="hidden" NAME="ID" VALUE="(.*)"', response)[0]
		# send username
		self.logger.debug("sending username")
		assert "user" in response.lower(), response
		response = self.make_request([('ID', session_id), ('STATE', "1"), ('DATA', self.username)])
		# send password
		self.logger.debug("sending password")
		assert "password" in response.lower(), response
		response = self.make_request([('ID', session_id), ('STATE', "2"), ('DATA', self.password)])
		if "denied" in response:
			raise ConnectionException(re.findall('FireWall-1 message: (.*)', response)[0].strip())
		else:
			self.info(re.findall('FireWall-1 message: (.*)', response)[0].strip())
		return session_id

	def open_firewall(self):
		self.info("opening firewall...")
		try:
			session_id = self.authenticate()
			# open request
			self.logger.debug("sending 'sign-on' request")
			self.make_request([('ID', session_id), ('STATE', "3"), ('DATA', "1")])
			self.connected(connected=True)
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
			self.connected(connected=False)
		except ConnectionException, e:
			self.error(str(e))

# ---------------
# display

	def connected(self, connected=True):
		self.firewall_open = connected
		if connected:
			self.statistics.firewall_open()
			self.logger.debug("opened")
			self.systrayicon.set_icon(get_icon("green"), "connection open")
		else:
			self.statistics.firewall_closed()
			self.logger.debug("closed")
			self.systrayicon.set_icon(get_icon("orange"), "connection closed")

	def error(self, text):
		self.logger.error(text)
		self.systrayicon.set_icon(get_icon("red"), text)
		self.statistics.firewall_error(text)

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
