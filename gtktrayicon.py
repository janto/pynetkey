#! /usr/bin/python
import gtk
import egg.trayicon

class GtkTrayIcon:
	def button_press_callback(self, widget, event):
		#~ try:
		if event.type == gtk.gdk._2BUTTON_PRESS:
			self.toggle_function(event)
		elif event.button == 3:
			self.menu.popup(None,None,None,event.button,event.time)

	def set_icon(self, icon, hover_text=None):
		if hover_text is not None:
			self.tooltips = gtk.Tooltips()
			self.tooltips.set_tip(self.icon, hover_text)
		self.image.set_from_file(icon)

	def set_hover_text(self, text):
		self.tooltips = gtk.Tooltips()
		self.tooltips.set_tip(self.icon, text)

	def construct(self, menu_options, on_quit=lambda s:None, startup=None):
		menu_options.append(("Quit", None, lambda a: on_quit()))
		# creates the tray icon
		self.icon = egg.trayicon.TrayIcon("inetkey")
		# uses a eventbox cause we cannot attach signals to a gtk.Image
		self.eventbox = gtk.EventBox()
		self.icon.add(self.eventbox)
		self.image = gtk.Image()
		self.image.set_from_file("icons/orange.ico")
		#~ self.image = gtk.image_new_from_stock("gtk-apply", gtk.ICON_SIZE_SMALL_TOOLBAR)
		self.eventbox.add(self.image)
		# connects the button pressed signal
		self.eventbox.connect("button_press_event", self.button_press_callback)
		# creates tooltips and attaches it to the icon
		self.tooltips = gtk.Tooltips()
		self.tooltips.set_tip(self.icon, 'pynetkey')
		self.icon.show_all()
		# creates the menu and adds items
		self.menu = gtk.Menu()
		self.toggle_function = menu_options[0][2]
		for text, _, action in menu_options:
			if text == "-":
				item = gtk.SeparatorMenuItem()
			else:
				item = gtk.MenuItem(text)
				item.connect("activate", action)
			item.show()
			self.menu.append(item)
		if startup:
			startup(self)
		# runs the main loop
		
		gtk.threads_init()
		gtk.threads_enter()
		gtk.main()
		gtk.threads_leave()

import time
import os.path
from ConfigParser import ConfigParser
def prompt_username_password():
	config = ConfigParser()
	filename = os.path.expanduser("~/.inetkeyrc")
	try:
		assert os.path.exists(filename), "can't find '%s'" % filename
		config.read(filename)
		return config.get("config", "username"), config.get("config", "password")
	except Exception, e:
		print e
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
		
		self.read_ready = Event()

		self.window = gtk.Window(gtk.WINDOW_TOPLEVEL)
		
		self.window.set_title("Enter Info")
		
		self.window.connect("delete_event", self.delete_event)
		
		self.window.set_border_width(10)
		
		self.column = gtk.VBox(False, 0)
		
		self.row1 = gtk.HBox(False, 0)
		self.row2 = gtk.HBox(False, 0)
		#self.row3 = gtk.HBox(False, 0)
		
		self.userLabel = gtk.Label("Username:")
		self.userText = gtk.Entry()
		self.passwordLabel = gtk.Label("Password:")
		self.passwordText = gtk.Entry()
		self.passwordText.set_visibility(False)
		self.connectButton = gtk.Button("Connect")
		
		self.row1.pack_start(self.userLabel, True, True, 0)
		self.row1.pack_start(self.userText, True, True, 0)
		self.row2.pack_start(self.passwordLabel, True, True, 0)
		self.row2.pack_start(self.passwordText, True, True, 0)
		
		self.window.add(self.column)
		self.column.pack_start(self.row1, True, True, 0)
		self.column.pack_start(self.row2, True, True, 0)
		
		self.connectButton.connect("clicked", self.callback, "'Connect' clicked!")
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
		gtk.main()


if __name__ == '__main__':
	print prompt_username_password()
	menu_options = []
	base = GtkTrayIcon()
	menu_options.append(("Quit", None, gtk.main_quit))
	menu_options.append(("-", None, lambda a: None))
	menu_options.append(("change", None, lambda a: base.set_icon("icons/blue.ico", "connection")))
	base.construct(menu_options)
	base.set_icon("icons/green.ico")
