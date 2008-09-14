import wx

class TaskBarApp(wx.Frame):
	def __init__(self, parent, id, title):
		wx.Frame.__init__(self, parent, -1, title, size = (1, 1),
		    style=wx.FRAME_NO_TASKBAR|wx.NO_FULL_REPAINT_ON_RESIZE)
		self.tbicon = wx.TaskBarIcon()
		icon = wx.Icon("icons/orange.ico", wx.BITMAP_TYPE_ICO)
		self.tbicon.SetIcon(icon, '')
		self.tbicon.Bind(wx.EVT_TASKBAR_LEFT_DCLICK, self.OnTaskBarLeftDClick)
		self.tbicon.Bind(wx.EVT_TASKBAR_RIGHT_UP, self.OnTaskBarRightClick)
		self.Show(True)

	def OnTaskBarLeftDClick(self, evt):
		print "dblL"

	def OnTaskBarRightClick(self, evt):
		print "R"
		self.tbicon.Destroy()
		self.Close(True)
		wx.GetApp().ProcessIdle()

class TrayIcon(wx.App):
	def __init__(self):
		self.startup = None
		wx.App.__init__(self, 0)
	
	def OnInit(self):
		self.frame = TaskBarApp(None, -1, ' ')
		self.frame.Center(wx.BOTH)
		self.frame.Show(False)
		return True

	def construct(self, menu_options=None, startup=None, on_quit=None):
		self.startup = startup
		self.startup(self)
		print 2
		self.MainLoop()
		#~ if on_quit is not None:
			#~ on_quit()

	def set_icon(self, filename, text=None):
		icon = wx.Icon(filename, wx.BITMAP_TYPE_ICO)
		self.frame.tbicon.SetIcon(icon, text)
	
	def set_hover_text(self, text):
		pass

def prompt_username_password():
	return "user", "pass"

def main():
	tray = TrayIcon()
	tray.construct()

if __name__ == '__main__':
	#~ main()
	import pynetkey
	pynetkey.main()
