#!/bin/bash

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

for f in lib/* extras.d/* exercises/*; do
    echo "Installing symlink for $f"
    rm ../../../devstack/$f || true
    ln -s $DIR/$f ../../../devstack/$f
done
