#!/bin/bash

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
OUTER_DIR=$($DIR/abs.sh $DIR/../../)

echo $OUTER_DIR

mkdir -p $OUTER_DIR/out
GIT_USER_NAME=$(git config user.name)
GIT_USER_EMAIL=$(git config user.email)

docker run -ti \
  -e "GIT_USER_NAME=${GIT_USER_NAME}" \
  -e "GIT_USER_EMAIL=${GIT_USER_EMAIL}" \
  -v $OUTER_DIR/out:/root/out \
  -v $OUTER_DIR/ib:/root/ib \
  ib \
  /bin/bash -c "/root/ib/scripts/start.sh && zsh"
