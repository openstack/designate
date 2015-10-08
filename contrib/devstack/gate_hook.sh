#!/bin/bash

set -ex

cd /opt/stack/new/designate/devstack/gate
./gate_hook.sh
