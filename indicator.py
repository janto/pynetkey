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

	#~ help(appindicator)
	#~ 1/0

	menu = gtk.Menu()

	def toggle_connection_state(menu_item, ind):
		status = service.status()
		if status == "open":
			service.close()
		else:
			service.open()

	usage_menu_item = None
	msg_menu_item = None
	for title, icon, callback in [
		("Toggle FireWall", None, toggle_connection_state),
		("Open Firewall", get_icon("green"), lambda m,ind: service.open()),
		("Close Firewall", get_icon("orange"), lambda m,ind: service.close()),
		("-", None, None),
		("Change User", None, change_user),
		("Edit Config File", None, lambda m,ind: open_url(config_filename)),
		("-", None, None),
		("User Admin", None, lambda m,ind: open_url('http://www.sun.ac.za/useradm')),
		("Firewall Usage", None, lambda m,ind: open_url('https://maties2.sun.ac.za/fwusage/')),
		("IT Website", None, lambda m,ind: open_url('http://it.sun.ac.za/')),
		("-", None, None),
		("msg", None, None),
		("usage", None, None),
		("-", None, None),
		("Quit", None, lambda m,ind: gtk.main_quit()),
		]:

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

	stop_event = threading.Event()

	def monitor_status(stop_event=stop_event, usage_menu_item=usage_menu_item):
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

				msg = service.last_message_from_server()
				msg_menu_item.set_label(msg)

				usage = service.usage()
				usage_menu_item.set_label(usage)

			except dbus.DBusException:
				ind.set_icon("pynetkey-error")
			finally:
				gtk.gdk.threads_leave()

			time.sleep(0.75)
			if stop_event.isSet():
				break

	thread = threading.Thread(target=monitor_status)
	thread.start()

	try:
		gtk.main()
	finally:
		stop_event.set()

if __name__ == "__main__":
	main()
