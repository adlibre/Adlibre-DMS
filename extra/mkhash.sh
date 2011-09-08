#!/bin/bash

# Script to create hashes for testing purposes

SECRET_KEY='z@ndqd972=9vmw0_5i^y!zwo59sxu*yru#3)5&4l*$eokb6_bp'

DOCS='abcde888 abcde999'

for d in $DOCS; do
  F=`echo -n $d${SECRET_KEY}|md5`
  echo $F
done
