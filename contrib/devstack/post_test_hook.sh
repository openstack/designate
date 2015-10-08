#!/bin/bash

set -ex

cd /opt/stack/new/designate/devstack/gate
./post_test_hook.sh
