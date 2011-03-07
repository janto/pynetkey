rm -rf pynetkey
hg clone . pynetkey
echo -e "[paths]\ndefault = static-http://dip.sun.ac.za/~janto/pynetkey/repo" > pynetkey/.hg/hgrc
tar -cvvzf pynetkey.tar.gz pynetkey
rm -rf pynetkey
