#!/bin/bash
export DISPLAY=:0
$(dirname $0)/pynetkeyd.py "$@"
