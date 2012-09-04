#!/usr/bin/env python

"""

This script is a minimal console version of pynetkey -- which is inetkey written in Python.
http://bitbucket.org/janto/pynetkey

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

WARNING: This script does not do any authentication of the server's certificate. It might even be sending the login details unencrypted. Probably not, but I haven't checked it out in detail.
Also, pynetkey is not supported by IT, but feel free to contact me if there is any problem.
- Janto (jantod@gmail.com)

History
------
Updated to use open2/close2 calls - Janto (Sep 2012)
Report usage - Janto (Apr 2012)
New xmlrpc interface to firewall - Janto (Mar 2012)
Authentication failure handling and retries - Janto (Mar 2012)
More minor error handling - Janto (Mar 2011)
Minor error handling - Janto (Sep 2010)
Firewall changed to TLS - Janto (Jun 2010)
Add some informative messages - Janto (Apr 2010)
Placed under GPL - Janto (Dec 2009)
Config file path can include "~" - Janto (Sep 2009)
Optional load from config file - Janto (Jul 2009)
Now also sends client version details on connect, to future proof things - Janto (Apr 2009)
Changed address from fw0.sun.ac.za to fw.sun.ac.za for SCN users - Janto (Oct 2008)
Only prompt for a password if we have a username - NM (Feb 2007)
Initial version - Janto (Nov 2005)

"""

reconnection_delay = 60*10
#~ connection_timeout = 15
version = "pynetkey cli 20120905"

import socket
import ssl
#~ socket.setdefaulttimeout(connection_timeout) # global timeout
import logging

import stat
import signal
from optparse import OptionParser
from time import sleep
from getpass import getpass

import xmlrpclib

import ConfigParser
import base64
import os
import traceback

logging.root.setLevel(logging.INFO)
log_format = "%(name)s@%(asctime)s: %(message)s"
logging.basicConfig(
	level=logging.DEBUG,
	datefmt="%H:%M",
	format=log_format,
	)
logger = logging.getLogger("Inetkey")

default_firewall_url = "https://maties2.sun.ac.za:443/RTAD4-RPC3"

def load_username_password(config_filename):
	username = None
	password = None

	config_filename = os.path.expanduser(config_filename)
	if not os.path.exists(config_filename):
		logger.error("file does not exist: %s\n" % config_filename)
		return username, password

	# make file user-level read/write only
	os.chmod(config_filename, stat.S_IRUSR | stat.S_IWUSR)

	# process config file
	config = ConfigParser.ConfigParser()
	config.read(config_filename)
	try:
		username = config.get("config", "username")
		password = config.get("config", "password")
	except ConfigParser.NoSectionError:
		print "error loading username/password"
	else:
		if password: # provided as plaintext
			encoded_password = base64.b32encode(password)
			config.set("config", "encoded_password_b32", encoded_password)
			config.set("config", "password", "") # clear plaintext
			# save encoded password
			f = file(config_filename, "w")
			config.write(f)
			f.close()

		else:
			encoded_password = config.get("config", "encoded_password_b32")
			password = base64.b32decode(encoded_password)

	return username, password

class ConnectionException(Exception):
	pass

class AccessDeniedException(Exception):
	pass

class Inetkey(object):

	def __init__(self, username, password):
		self.username = username
		self.password = password
		self.firewall_open = False
		self.status = {}
		self.proxy = xmlrpclib.ServerProxy(default_firewall_url, verbose=False)
		logger.warn("Pynetkey does not currently authenticate the server certificate")

	def network_action(self, function, data):
		try:
			self.status = function(data)
			resultmsg = self.status.get("resultmsg", "")
			if self.status.get("resultcode") != 0:
				if "rejected" in resultmsg or "password" in resultmsg:
					raise AccessDeniedException(resultmsg)
				raise ConnectionException(resultmsg)
			logger.info(resultmsg) # probably "Success"
			if "monthusage" in self.status:
				logger.info("monthusage: R%0.2f" % self.status["monthusage"])
			if "monthbytes" in self.status:
				logger.info("monthbytes: %d MB" % (self.status["monthbytes"]/1024.0/1024.0))
		except (ssl.SSLError, socket.error, xmlrpclib.Error), e:
			raise ConnectionException(e)

	def open_firewall(self):
		logger.info("opening firewall...")
		self.network_action(self.proxy.rtad4inetkey_api_open2, dict(requser=self.username, reqpwd=self.password, platform="any", keepalive=0))
		self.set_connected_status(connected=True)

	def close_firewall(self):
		logger.info("closing firewall...")
		self.network_action(self.proxy.rtad4inetkey_api_close2, dict(requser=self.username, reqpwd=self.password, platform="any"))
		self.set_connected_status(connected=False)

	def set_connected_status(self, connected=True):
		self.firewall_open = connected
		if connected:
			logger.info("firewall open. press <Ctrl> C to close")
		else:
			logger.info("firewall closed")

def main():
	# parse arguments
	parser = OptionParser()
	parser.add_option("-u", "--user", dest="username", help="", metavar="USERNAME")
	parser.add_option("-c", "--config", dest="config", help="loads username/password from file", metavar="CONFIG")
	parser.add_option("-r", "--retries", type="int", dest="retries", help="number of renew retries to do before aborting (default=1)", default=1, metavar="RETRIES")
	options, args = parser.parse_args()

	username = options.username
	password = None

	if options.config:
		username, password = load_username_password(options.config)

	if username and not password:
		try:
			password = getpass()
		except (KeyboardInterrupt, EOFError):
			password = "" # empty
	if not username or not password \
			or '\x03' in password: # Due to a python bug http://bugs.python.org/issue11236 , ctrl-c is not caught so at least check for its code
		print "Version:", version
		parser.print_help()
		return

	inetkey = Inetkey(username, password)
	# open
	try:
		inetkey.open_firewall()
	except AccessDeniedException, e:
		logger.warn(e)
		return
	# renew
	retries_left = options.retries + 1 # plus one for initial
	while 1:
		if retries_left <= 0:
			logger.info("too many failures. giving up.")
			break
		retries_left -= 1
		try:
			while 1:
				sleep(reconnection_delay)
				inetkey.open_firewall()
				retries_left = options.retries # reset retries on success
		except (KeyboardInterrupt, EOFError):
			break
		except ConnectionException, e:
			logger.warn(e)
			traceback.print_exc()
	# close
	inetkey.close_firewall()

if __name__ == '__main__':
	main()
