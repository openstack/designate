#!/bin/bash

SOURCE_DIR=$(readlink -e $(dirname $(readlink -f $0)))
DEVSTACK_DIR=$(pwd -P)

pushd $SOURCE_DIR >> /dev/null

for path in lib/* extras.d/* exercises/*; do
    if [ ! -e "$DEVSTACK_DIR/$path" ]; then
        echo "Installing symlink for $path"
        ln -fs $SOURCE_DIR/$path $DEVSTACK_DIR/$path
    fi
done

popd >> /dev/null
