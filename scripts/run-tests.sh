#!/bin/bash

set -e
for f in test/*-test.py test/**/*-test.py
do
  if [ -f $f ]; then
    python $f
  fi
done
