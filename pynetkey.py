#!/usr/bin/env python

"""Inetkey in Python.

	Janto Dreijer <janto@sun.ac.za>

"""

from __future__ import division

import urllib2, urllib
import logging
import re
import signal
from threading import Thread, Timer, Event
from time import localtime, strftime, sleep
from datetime import timedelta, datetime
import os
import platform

import sys
import os.path

if platform.system() in ("Windows", "Microsoft"):
	import win32api
	from systrayicon import prompt_username_password, TrayIcon
	def gui_quit():
		pass
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
		
elif platform.system() == "Linux":
	from gtktrayicon import prompt_username_password
	from gtktrayicon import GtkTrayIcon as TrayIcon
	from gtk import main_quit as gui_quit
	def open_url(url):
		os.system('gnome-open %s' % url)
	def workstation_is_locked():
		return False
else:
	raise Exception(platform.system()+" not supported")

refresh_frequency = 9*60
#~ refresh_frequency = 1.0
usage_query_frequency = 1*60

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

def get_icon(name):
	return os.path.join(os.path.dirname(os.path.abspath(__file__)), "icons/%s.ico" % name)

def get_usage(username, password):
	url = "https://maties2.sun.ac.za/fwusage/"

	class FancyURLopener(urllib.FancyURLopener):
		def prompt_user_passwd(self, a, b):
			return username, password
		
	opener = FancyURLopener(proxies={})
	result = opener.open(url)
	data = result.read()
	return re.findall('<td align="right"><font size="1">(.*)</font></td>', data)[-1]

class Statistics(object):

	def __init__(self):
		self.open_events = []
		self.close_events = []
		self.error_events = []

	def firewall_open(self):
		self.open_events.append(localtime())

	def firewall_closed(self):
		self.close_events.append(localtime())

	def firewall_error(self, text):
		self.error_events.append((localtime(), text))

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

	def dump_to_file(self, filename="stats.txt"):
		f = file(filename, "a+")
		f.write("%s\n" % self)
		f.close()
		f = file("opens.txt", "w")
		f.write("\n".join([" ".join(str(t)) for t in self.open_events]))
		f.close()
		f = file("closes.txt", "w")
		f.write("\n".join([" ".join(str(t)) for t in self.close_events]))
		f.close()
		f = file("errors.txt", "w")
		f.write("\n".join([" ".join(str(t)) for t in self.error_events]))
		f.close()

class Inetkey(object):

	def __init__(self, username, password, open_on_launch=True):
		self.logger = logging.getLogger("Inetkey")
		self.statistics = Statistics()
		self.url = "https://fw0.sun.ac.za:950"
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
			try:
				self.systrayicon.set_hover_text("R%s" % get_usage(self.username, self.password))
			except Exception, e:
				self.systrayicon.set_hover_text(str(e))
				#~ self.systrayicon.set_hover_text("cannot determine firewall usage")
		self.usage_checker = ReTimer(usage_query_frequency, check_usage, immediate=True)
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

	def shutdown(self):
		self.refresher.stop()
		self.usage_checker.stop()
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
			username, password = prompt_username_password()
			if username and password:
				self.close_firewall()
				self.username, self.password = username, password
				self.open_firewall()
		def toggle_close_on_workstation_locked(sysTrayIcon):
			self.close_on_workstation_locked = not self.close_on_workstation_locked
			#~ self.logger.info("close_on_workstation_locked=%s" % self.close_on_workstation_locked)
			#~ print "close_on_workstation_locked=%s" % self.close_on_workstation_locked

		#~ menu_options.append(("Toggle FireWall", None, toggle_connection_state))
		#~ menu_options.append(("Open FireWall", get_icon("green"), lambda a: self.open_firewall()))
		#~ menu_options.append(("Close FireWall", get_icon("orange"), lambda a: self.close_firewall()))
		#~ menu_options.append(("-", None, None))
		#~ menu_options.append(("Close on Workstation Lock", lambda: self.close_on_workstation_locked, toggle_close_on_workstation_locked))
		#~ menu_options.append(("Change user...", None, change_user))
		#~ menu_options.append(("-", None, None))
		#~ menu_options.append(("User admin page...", None, lambda a: win32api.ShellExecute(0,None,"http://www.sun.ac.za/useradm",None,None,1)))
		#~ menu_options.append(("Tariff structure...", None, lambda a: win32api.ShellExecute(0,None,"http://infoteg.sun.ac.za/infoteg/IN_Tariewe_E.htm",None,None,1)))
		#~ menu_options.append(("-", None, None))
		#~ menu_options = tuple(menu_options)
		#~ SysTrayIcon(get_icon("blue"), "pynetkey", menu_options, on_quit=on_quit, default_menu_index=0, call_on_startup=self.startup)
		menu_options = []
		menu_options.append(("Toggle FireWall", None, toggle_connection_state))
		menu_options.append(("Open FireWall", get_icon("green"), lambda a: self.open_firewall()))
		menu_options.append(("Close FireWall", get_icon("orange"), lambda a: self.close_firewall()))
		menu_options.append(("-", None, None))
		menu_options.append(("Close on Workstation Lock", lambda: self.close_on_workstation_locked, toggle_close_on_workstation_locked))
		menu_options.append(("Change user...", None, change_user))
		menu_options.append(("-", None, None))
		menu_options.append(("User admin page...", None, lambda a: open_url('http://www.sun.ac.za/useradm')))
		menu_options.append(("Firewall usage...", None, lambda a: open_url('https://maties2.sun.ac.za/fwusage/')))
		menu_options.append(("Tariff structure...", None, lambda a: open_url('http://infoteg.sun.ac.za/infoteg/IN_Tariewe_E.htm')))
		menu_options.append(("-", None, None))
		self.systrayicon.construct(menu_options, startup=self.startup, on_quit=on_quit)

# ---------------
# networking

	def make_request(self, variables=[]):
		try:
			if variables:
				request = urllib2.Request(url=self.url, data=urllib.urlencode(variables))
			else:
				request = urllib2.Request(url=self.url)
			#~ self.logger.debug(request.get_data())
			response = urllib2.HTTPSHandler().https_open(request).read()
		except Exception, e:
			#~ self.logger.warn(str(e).strip() or "no error message")
			raise ConnectionException(str(e))
		assert "ERROR" not in response, response
		return response

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
			self.logger.info("open")
			self.systrayicon.set_icon(get_icon("green"), "connection open")
		else:
			self.statistics.firewall_closed()
			self.logger.info("closed")
			self.systrayicon.set_icon(get_icon("orange"), "connection closed")

	def error(self, text):
		self.logger.error(text)
		self.systrayicon.set_icon(get_icon("red"), text)
		self.statistics.firewall_error(text)

	def warn(self, text):
		self.logger.warn(text)
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

if __name__ == '__main__':
	logging.root.setLevel(logging.WARN)
	logging.basicConfig(format="%(levelname)s@%(asctime)s=%(name)s:%(message)s", datefmt="%Y-%M-%d %H:%m")
	main()
