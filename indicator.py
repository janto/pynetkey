import gobject
import gtk
gtk.gdk.threads_init()
import appindicator

import dbus
import dbus.service
import dbus.glib

import threading
import time

bus_name = "za.ac.sun.pynetkey"
object_path = "/za/ac/sun/pynetkey/system"

def get_icon(name):
	return "/usr/share/pixmaps/%s.svg" % name

def change_user():
	pass

def main():
	bus = dbus.SessionBus()
	try:
		proxy = bus.get_object(bus_name, object_path)
	except dbus.exceptions.DBusException:
		service = None
	else:
		service = dbus.Interface(proxy, bus_name)
	assert service is not None

	#~ ind = appindicator.Indicator("Pynetkey", "indicator-messages", appindicator.CATEGORY_APPLICATION_STATUS)
	ind = appindicator.Indicator("Pynetkey", "pynetkey-main", appindicator.CATEGORY_APPLICATION_STATUS)
	#~ ind.set_status(appindicator.STATUS_ATTENTION)
	ind.set_status(appindicator.STATUS_ACTIVE)
	ind.set_attention_icon("indicator-messages-new")

	menu = gtk.Menu()

	def toggle_connection_state(menu_item, ind):
		status = service.status()
		if status == "open":
			service.close()
		else:
			service.open()

	for title, icon, callback in [
		("Toggle FireWall", None, toggle_connection_state),
		("Open Firewall", get_icon("green"), lambda m,ind: service.open()),
		("Close Firewall", get_icon("orange"), lambda m,ind: service.close()),
		("-", None, None),
		("Change User", None, change_user),
		("Edit Config File", None, lambda e: open_url(config_filename)),
		("-", None, None),
		("User Admin", None, lambda e: open_url('http://www.sun.ac.za/useradm')),
		("Firewall Usage", None, lambda e: open_url('https://maties2.sun.ac.za/fwusage/')),
		("IT Website", None, lambda e: open_url('http://it.sun.ac.za/')),
		("-", None, None),
		("Quit", None, None),
		]:

		menu_items = gtk.MenuItem(title)

		menu.append(menu_items)

		if callback:
			menu_items.connect("activate", callback, ind)

		menu_items.show()

	ind.set_menu(menu)

	def monitor_status():
		while 1:

			gtk.gdk.threads_enter()
			try:
				status = service.status()
				print status
				if status == "open":
					ind.set_icon("pynetkey-open")
				elif status == "closed":
					ind.set_icon("pynetkey-closed")
				else:
					assert False, status
			except dbus.DBusException:
				ind.set_icon("pynetkey-error")
			finally:
				gtk.gdk.threads_leave()

			time.sleep(0.75)

	thread = threading.Thread(target=monitor_status)
	thread.start()

	gtk.main()

if __name__ == "__main__":
	main()
