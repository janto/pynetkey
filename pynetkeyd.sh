#!/bin/bash
export DISPLAY=:0
python /usr/share/pyshared/pynetkey/pynetkeyd.py "$@"
