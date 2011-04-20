#!/bin/bash

CWD=$(cd ${0%/*} && pwd -P)

kill `pgrep -f "python ${CWD}/../src/dms/manage.py"`

