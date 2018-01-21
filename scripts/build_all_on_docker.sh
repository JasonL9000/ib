#!/bin/bash

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
OUTER_DIR=$($DIR/abs.sh $DIR/../../)

docker run -ti \
  -v $OUTER_DIR/out:/root/out \
  -v $OUTER_DIR/ib:/root/ib \
  ib /bin/bash scripts/build_all_on_linux.sh
