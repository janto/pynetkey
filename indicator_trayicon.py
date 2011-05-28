import gobject
import gtk
gtk.gdk.threads_init()
import appindicator

class TrayIcon:
	def construct(self, menu_options, startup=None, on_quit=None):

		#~ ind = appindicator.Indicator("Pynetkey", "indicator-messages", appindicator.CATEGORY_APPLICATION_STATUS)
		ind = appindicator.Indicator("Pynetkey", "pynetkey-main", appindicator.CATEGORY_APPLICATION_STATUS)
		#~ ind.set_status(appindicator.STATUS_ATTENTION)
		ind.set_status(appindicator.STATUS_ACTIVE)
		ind.set_attention_icon("indicator-messages-new")

		#~ help(appindicator)
		#~ 1/0

		menu = gtk.Menu()

		for title, icon, callback in menu_options:

			if title == "-":
				menu_item = gtk.SeparatorMenuItem()
			else:
				menu_item = gtk.MenuItem(title)

			if title == "usage":
				menu_item.set_label("<usage>")
				menu_item.set_can_focus(False)
				usage_menu_item = menu_item

			if title == "msg":
				menu_item.set_label("<msg>")
				menu_item.set_can_focus(False)
				msg_menu_item = menu_item

			menu.append(menu_item)

			if callback:
				menu_item.connect("activate", callback, ind)

			menu_item.show()

		ind.set_menu(menu)

		if startup:
			startup(self)
		# run the main loop
		gtk.main()

	def set_icon(self, filename, text):
		print "set_icon: %s %s" %(filename, text)

def main():
	pass

if __name__ == "__main__":
	main()