C:\Python25\python.exe setup.py py2exe --bundle 1
rmdir /Q /S pynetkey
rename dist pynetkey
del pynetkey.zip
"C:\Program Files\7-Zip\7z.exe" a pynetkey.zip pynetkey
