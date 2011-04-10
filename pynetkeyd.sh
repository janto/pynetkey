#!/bin/bash
export DISPLAY=:0
$(dirname $(readlink -n $0))/pynetkeyd.py "$@"
