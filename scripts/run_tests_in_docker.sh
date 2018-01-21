#!/bin/bash

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
ROOT=$($DIR/abs.sh $DIR/../)

# if ib container does not exist yet, do a build which will
# run the tests
if [ -z "$(docker images --filter 'reference=ib' -q)" ]; then
  $DIR/build.sh
else
  docker run -ti \
    -v $ROOT:/root/ib \
    ib \
    /bin/bash -c "/root/ib/scripts/run_tests.sh"
fi

