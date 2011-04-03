#!/bin/bash

CWD="`dirname $0`/";

kill `pgrep -f "python ${CWD}../src/dms/manage.py"`

