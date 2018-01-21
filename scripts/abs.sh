#!/bin/bash

CURRENT=$(pwd)
DIR=$(echo "${1%/*}")
(cd "$DIR" && echo "$(pwd -P)")
cd $CURRENT
