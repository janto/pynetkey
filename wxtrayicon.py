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

#XXX busy. not yet working.

import wx

class TaskBarIcon(wx.TaskBarIcon):
	"""
	Adds a Task Bar Icon to the System Tray. Right clicking on this
	will launch a menu, which will allow the user to close the application.
	"""
	TBMENU_RESTORE = wx.NewId()
	TBMENU_CLOSE   = wx.NewId()
	def __init__(self, frame, menu_options=None, on_quit=None):
		wx.TaskBarIcon.__init__(self)

		self.frame = frame
		self.menu_options = menu_options
		self.on_quit = on_quit
		self.callbacks = None

		# Bind to events
		self.Bind(wx.EVT_TASKBAR_LEFT_DCLICK, self.OnTaskBarActivate)
		#~ self.Bind(wx.EVT_MENU, self.OnTaskBarActivate, id=self.TBMENU_RESTORE)
		self.Bind(wx.EVT_MENU, self.OnTaskBarClose, id=self.TBMENU_CLOSE)

		#~ self.SetIcon(wx.Icon('icon.png', wx.BITMAP_TYPE_PNG), "Icon")

	def CreatePopupMenu(self):
		"""
		This method is called by the base class when it needs to popup
		the menu for the default EVT_RIGHT_DOWN event.  Just create
		the menu how you want it and return it from this function,
		the base class takes care of the rest.
		"""
		menu = wx.Menu()
		self.callbacks = {}
		for menu_option in self.menu_options:
			text, icon, callback = menu_option
			if text == "-":
				menu.AppendSeparator()
				continue

			id = wx.NewId()
			new = wx.MenuItem(menu, id, text)
			if icon is not None:
				try:
					if not callable(icon):
						new.SetBitmap(wx.Bitmap(icon))
				except:
					print(icon)
					raise
			menu.AppendItem(new)

			self.callbacks[id] = callback
			self.Bind(wx.EVT_MENU, self.OnTaskBarActivate, id=id)
		menu.Append(self.TBMENU_CLOSE,   "Quit")

		return menu

	def OnTaskBarActivate(self, evt):
		#~ print "activate", dir(evt)
		callback = self.callbacks[evt.GetId()]
		callback(self)
		#~ self.frame.Show()
		#~ self.frame.Raise()

	def OnTaskBarClose(self, evt):
		self.on_quit(None)
		self.frame.Close()
		self.Destroy()
		wx.GetApp().ProcessIdle()

class TaskBarApp(wx.Frame):

	def __init__(self, parent, id, title, menu_options, on_quit=None):
		wx.Frame.__init__(self, parent, -1, title, size = (1, 1),
		    style=wx.FRAME_NO_TASKBAR|wx.NO_FULL_REPAINT_ON_RESIZE)
		self.tbicon = TaskBarIcon(frame=self, menu_options=menu_options, on_quit=on_quit)
		self.tbicon.Bind(wx.EVT_TASKBAR_LEFT_DCLICK, self.OnTaskBarLeftDClick)
		#~ self.tbicon.Bind(wx.EVT_TASKBAR_RIGHT_UP, self.OnTaskBarRightClick)
		self.menu_options = menu_options

		#~ self.Show(True)

	def OnTaskBarLeftDClick(self, evt):
		text, icon, callback = self.menu_options[0]
		callback(self)

	#~ def OnTaskBarRightClick(self, evt):
		#~ print "R"
		#~ self.tbicon.Destroy()
		#~ self.Close(True)
		#~ wx.GetApp().ProcessIdle()

	def set_icon(self, filename, text=None):
		icon = wx.Icon(filename, wx.BITMAP_TYPE_ICO)
		self.tbicon.SetIcon(icon, text)

	def set_hover_text(self, text):
		pass

class TrayIcon(object):

	def __init__(self):
		self.app = None
		self.filename = "icons/orange.ico"

	def construct(self, menu_options=None, startup=None, on_quit=None):
		app = wx.App(0)
		self.app = app
		app.frame = TaskBarApp(None, -1, ' ', menu_options=menu_options, on_quit=on_quit)
		app.frame.Center(wx.BOTH)
		app.frame.Show(False)
		#~ self.set_icon()
		#~ print 1
		if startup is not None:
			startup(self)
		#~ print 2
		app.MainLoop()

	def set_icon(self, filename=None, text=None):
		if filename is not None:
			self.filename = filename
		self.app.frame.set_icon(filename=self.filename, text=text)

	def set_hover_text(self, text):
		#~ self.app.frame.set_hover_text(text=text)
		self.set_icon(text=text)

def gui_quit():
	pass
	#~ print "gui_quit"

class LoginDialog(wx.Dialog):
	def __init__(self, parent, id=-1, title="Login", pos=wx.DefaultPosition, size=wx.Size(250, 150)):

		wx.Dialog.__init__(self, parent, id, title, pos, size)
		wx.StaticText(self, -1, 'Please type your user name and password.', wx.Point(15, 5))
		wx.StaticText(self, -1, 'User name: ', wx.Point(20, 30))
		wx.StaticText(self, -1, 'Password: ', wx.Point(20, 55))

		self.nameBox = wx.TextCtrl(self, -1, '', wx.Point(100,30), wx.Size(120, -1))
		self.passwordBox = wx.TextCtrl(self, -1, '', wx.Point(100,55), wx.Size(120, -1), style=wx.TE_PASSWORD)
		wx.Button(self, wx.ID_OK, ' OK ', wx.Point(35, 90), wx.DefaultSize).SetDefault()
		wx.Button(self, wx.ID_CANCEL, ' Cancel ', wx.Point(135, 90), wx.DefaultSize)

	def GetUser(self):
		val = self.ShowModal()
		if val == wx.ID_OK:
			return self.nameBox.GetValue(), self.passwordBox.GetValue()
		else:
			return None, None

def password_dialog():
	app = wx.GetApp() or wx.App(0)
	main = wx.Frame(None, -1, "pynetkey prompt", size = (1, 1),
	    style=wx.FRAME_NO_TASKBAR|wx.NO_FULL_REPAINT_ON_RESIZE)
	app.SetTopWindow(main)
	login = LoginDialog(main)
	main.Center(wx.BOTH)
	main.Show(False)
	username, password = login.GetUser()
	#~ print username, password
	#~ app.MainLoop()
	main.Close()
	return username, password

def main():
	tray = TrayIcon()
	tray.construct()

if __name__ == '__main__':
	main()
	#~ import pynetkey
	#~ pynetkey.main()
