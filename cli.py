#!/usr/bin/env python

"""

This script is a minimal console version of pynetkey -- which is inetkey written in Python.

http://sulug.sun.ac.za/sulugwiki/pynetkey

WARNING: This script does not do any authentication of the server's certificate. It might even be sending the login details unencrypted. Maybe. Haven't checked it out in detail.
Also, pynetkey is not supported by IT, but feel free to contact me if there is any problem.
- Janto (jantod@gmail.com)

History
------
Now also sends client version details on connect to future proof things - Janto (Apr 2009)
Changed address from fw0.sun.ac.za to fw.sun.ac.za for SCN users - Janto (Oct 2008)
Only prompt for a password if we have a username - NM (Feb 2007)
Initial version - Janto (Nov 2005)

"""


reconnection_delay = 60*10
connection_timeout = 15
version = "pynetkey cli 20090416"
connection_url = "https://fw.sun.ac.za:950"

#~ import socket
#~ socket.setdefaulttimeout(connection_timeout) # global timeout
import urllib2, urllib
import logging
import re
import stat
import signal
from optparse import OptionParser
from time import sleep
from getpass import getpass

class ConnectionException(Exception):
	pass

class Inetkey(object):

	def __init__(self, username, password):
		self.logger = logging.getLogger("Inetkey")
		self.url = connection_url
		self.username = username
		self.password = password
		self.firewall_open = False

	def make_request(self, variables=[]):
		if variables:
			variables.insert(0, ("client", version)) # maybe IT will one day want to block a specific version?
			request = urllib2.Request(url=self.url, data=urllib.urlencode(variables))
		else:
			request = urllib2.Request(url=self.url)
		request.timeout = connection_timeout #XXX hack to make it work with python2.6
		response = urllib2.HTTPSHandler().https_open(request).read()
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

	def connected(self, connected=True):
		self.firewall_open = connected
		if connected:
			self.logger.info("firewall open")
		else:
			self.logger.info("firewall closed")

	def error(self, text):
		self.logger.error(text)

	def warn(self, text):
		self.logger.warn(text)

	def info(self, text):
		self.logger.info(text)

def main():
	# parse arguments
	parser = OptionParser()
	parser.add_option("-u", "--user", dest="username", help="", metavar="USERNAME")
	#~ options, args = parser.parse_args()
	#~ username = options.username
	username = "13662244"
	password = "f000000!"
	#~ password = getpass()
	if not (password and username):
		parser.print_help()
		return
	# create application
	inetkey = Inetkey(username, password)
	# detect shutdown/kill signals
	#~ signal.signal(signal.SIGINT, lambda signalnum, stack_frame: inetkey.close_firewall())
	#~ signal.signal(signal.SIGTERM, lambda signalnum, stack_frame: inetkey.close_firewall())
	# run
	try:
		while 1:
			inetkey.open_firewall()
			sleep(reconnection_delay)
	except (KeyboardInterrupt, EOFError):
		pass
	inetkey.close_firewall()

if __name__ == '__main__':
	logging.root.setLevel(logging.INFO)
	logging.basicConfig()
	main()