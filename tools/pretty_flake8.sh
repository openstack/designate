#!/bin/sh

TESTARGS=$1

exec 3>&1
status=$(exec 4>&1 >&3; ( flake8 ; echo $? >&4 ) | python tools/pretty_flake8.py) && exit $status
