"""Pynetkey

the version number is shown in the title bar of the password dialog box.

it is also sent with each http request in case IT one day decides to block a specific version
this is especially important for the get_usage requests. because it's done every minute, the traffic might become significant if pynetkey's usage spreads.
yeah, I'm paranoid.
"""
version = "20110301"
