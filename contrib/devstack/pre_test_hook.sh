#!/bin/bash

set -ex

# Install designate devstack integration
pushd $BASE/new/designate/contrib/devstack

for f in lib/* extras.d/* exercises/*; do
    if [ ! -e "$BASE/new/devstack/$f" ]; then
        echo "Installing: $f"
        cp -r $f $BASE/new/devstack/$f
    fi
done

popd
