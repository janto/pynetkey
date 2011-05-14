import gobject
import gtk
import appindicator

def toggle_connection_state(menu_item, ind):
	#~ ind.set_icon("indicator-messages-new")
	ind.set_icon("icons/green.svg")

def get_icon(name):
	return None

def change_user():
	pass

def main():
	ind = appindicator.Indicator("Pynetkey", "indicator-messages", appindicator.CATEGORY_APPLICATION_STATUS)
	#~ ind.set_status(appindicator.STATUS_ATTENTION)
	ind.set_status(appindicator.STATUS_ACTIVE)
	ind.set_attention_icon("indicator-messages-new")

	menu = gtk.Menu()

	for title, icon, callback in [
		("Toggle FireWall", None, toggle_connection_state),
		("Open Firewall", get_icon("green"), lambda e: self.open_firewall()),
		("Close Firewall", get_icon("orange"), lambda e: self.close_firewall()),
		("-", None, None),
		("Change User", None, change_user),
		("Edit Config File", None, lambda e: open_url(config_filename)),
		("-", None, None),
		("User Admin", None, lambda e: open_url('http://www.sun.ac.za/useradm')),
		("Firewall Usage", None, lambda e: open_url('https://maties2.sun.ac.za/fwusage/')),
		("IT Website", None, lambda e: open_url('http://it.sun.ac.za/')),
		("-", None, None),
		]:

		menu_items = gtk.MenuItem(title)

		menu.append(menu_items)

		if callback:
			menu_items.connect("activate", callback, ind)

		menu_items.show()

	ind.set_menu(menu)

	gtk.main()

if __name__ == "__main__":
	main()
