import gobject
import gtk
gtk.gdk.threads_init()
import appindicator

class TrayIcon:

	def construct(self, menu_options, startup=None, on_quit=None):
		ind = appindicator.Indicator("Pynetkey", "pynetkey-main", appindicator.CATEGORY_APPLICATION_STATUS)
		self.ind = ind
		ind.set_status(appindicator.STATUS_ACTIVE)
		ind.set_attention_icon("indicator-messages-new")

		menu = gtk.Menu()

		menu_options.append(("Quit", None, on_quit))
		menu_options.append(("-", None, None))
		for title, icon, callback in menu_options:

			if title == "-":
				menu_item = gtk.SeparatorMenuItem()
			else:
				menu_item = gtk.MenuItem(title)
			menu.append(menu_item)

			if callback:
				def callback_wrapper(m, ind, callback=callback):
					#~ print callback
					callback(None) # event=None
				menu_item.connect("activate", callback_wrapper, ind)

			menu_item.show()

		self.msg_menu_item = gtk.MenuItem(title)
		self.msg_menu_item.set_can_focus(False)
		self.msg_menu_item.set_label("")
		self.msg_menu_item.show()
		menu.append(self.msg_menu_item)

		ind.set_menu(menu)

		#~ while gtk.events_pending(): # give gui time to update icon
			#~ gtk.main_iteration()

		if startup:
			#~ startup(self)
			gobject.idle_add(startup, self)
		# run the main loop
		gtk.main()

	def set_icon(self, filename, text=None):
		self.ind.set_icon(filename)
		if text:
			self.msg_menu_item.set_label(text)

	def set_hover_text(self, text):
		self.msg_menu_item.set_label(text)

def main():
	pass

if __name__ == "__main__":
	main()