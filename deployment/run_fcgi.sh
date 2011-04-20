#!/bin/bash
# requires flup

CWD=$(cd ${0%/*} && pwd -P)

. ${CWD}/../bin/activate
python ${CWD}/../src/dms/manage.py runfcgi protocol=scgi host=127.0.0.1 port=${1}
