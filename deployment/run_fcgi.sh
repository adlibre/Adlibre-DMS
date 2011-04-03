#!/bin/bash
# requires flup

CWD="`dirname $0`/";

. ${CWD}../bin/activate
python ${CWD}../src/dms/manage.py runfcgi protocol=scgi host=127.0.0.1 port=${1}

