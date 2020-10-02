#! /usr/bin/python

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


from . import __init__

import gtk
import gobject
gtk.gdk.threads_init()

#XXX theres quite a few threading issues here

class GtkTrayIcon(gtk.StatusIcon):
	def button_press_callback(self, widget, event):
		if event.type == gtk.gdk._2BUTTON_PRESS:
			self.toggle_function(event)
		elif event.button == 3:
			self.menu.popup(None,None,None,event.button,event.time)

	def set_icon(self, icon, hover_text=None):
		def _set_icon(icon=icon, hover_text=hover_text):
			#~ print "set_icon", icon, hover_text
			self.set_from_file(icon)
			#~ print "set", hover_text
			if hover_text is not None:
				self.set_tooltip_text(hover_text)
		#~ gtk.gdk.threads_enter()
		gobject.idle_add(_set_icon)
		#~ while gtk.events_pending(): # give gui time to update icon
			#~ gtk.main_iteration()
		#~ gtk.gdk.threads_leave()

	def set_hover_text(self, text):
		#~ print "text", text
		#~ gtk.gdk.threads_enter()
		gobject.idle_add(self.set_tooltip_text, text)
		#~ gtk.gdk.threads_leave()
		#~ while gtk.events_pending(): # give gui time to update icon
		#~ gtk.main_iteration()

	def construct(self, menu_options, on_quit=gtk.main_quit, startup=None):

		#~ gtk.gdk.threads_enter()

		# creates the tray icon
		self.set_from_file("icons/closed.ico")
		self.connect("button_press_event", self.button_press_callback) # connects the button pressed signal
		self.set_hover_text('pynetkey')

		# creates the menu and adds items
		menu_options.append(("Quit", None, on_quit))
		self.menu = gtk.Menu()
		default_item = 0
		self.toggle_function = menu_options[default_item][2]
		for text, icon, action in menu_options:
			if text == "-":
				item = gtk.SeparatorMenuItem()
			else:
				item = gtk.ImageMenuItem(text)
				if icon is not None:
					item.set_image(gtk.image_new_from_file(icon))
				item.connect("activate", action)
			item.show()
			self.menu.append(item)

		self.set_visible(True)

		#~ gtk.gdk.threads_leave()

		while gtk.events_pending(): # give gui time to update icon
			gtk.main_iteration()

		if startup:
			startup(self)
			#~ gobject.idle_add(startup, self)

		# run the main loop
		gtk.main()

def password_dialog():
	dialog = PasswordDialog()
	dialog.read_ready.wait()
	return dialog.username, dialog.password

from threading import Event
class PasswordDialog:
	def callback(self, widget, data):
		self.window.hide()
		self.username = self.userText.get_text()
		self.password = self.passwordText.get_text()
		self.read_ready.set()
		gtk.main_quit()
		return False

	def delete_event(self, widget, event, data=None):
		gtk.main_quit()
		return False

	def __init__(self):
		gtk.gdk.threads_enter()

		self.read_ready = Event()

		self.window = gtk.Window(gtk.WINDOW_TOPLEVEL)

		self.window.set_title("pynetkey %s" % __init__.version)

		self.window.connect("delete_event", self.delete_event)

		self.window.set_border_width(10)

		self.column = gtk.VBox(False, 0)

		self.row1 = gtk.HBox(False, 0)
		self.row2 = gtk.HBox(False, 0)
		#self.row3 = gtk.HBox(False, 0)

		self.userLabel = gtk.Label("Username:")
		self.userText = gtk.Entry()
		self.userText.connect("activate", self.callback, self.window)
		self.passwordLabel = gtk.Label("Password:")
		self.passwordText = gtk.Entry()
		self.passwordText.connect("activate", self.callback, self.window)
		self.passwordText.set_visibility(False)
		self.connectButton = gtk.Button("Connect")

		self.row1.pack_start(self.userLabel, True, True, 0)
		self.row1.pack_start(self.userText, True, True, 0)
		self.row2.pack_start(self.passwordLabel, True, True, 0)
		self.row2.pack_start(self.passwordText, True, True, 0)

		self.window.add(self.column)
		self.column.pack_start(self.row1, True, True, 0)
		self.column.pack_start(self.row2, True, True, 0)

		self.connectButton.connect("clicked", self.callback, self.window)
		self.column.pack_start(self.connectButton, True, True, 0)
		self.connectButton.show()

		self.userLabel.show()
		self.userText.show()
		self.passwordLabel.show()
		self.passwordText.show()
		self.connectButton.show()
		self.row1.show()
		self.row2.show()
		self.column.show()
		self.window.show()

		gtk.gdk.threads_leave()

		gtk.main()

if __name__ == '__main__':
	print(password_dialog())
	menu_options = []
	base = GtkTrayIcon()
	menu_options.append(("Quit with icon", "icons/blue.ico", gtk.main_quit))
	menu_options.append(("-", None, lambda a: None))
	menu_options.append(("blue", None, lambda a: base.set_from_file("icons/blue.ico")))
	menu_options.append(("green", None, lambda a: base.set_from_file("icons/green.ico")))
	base.construct(menu_options)
