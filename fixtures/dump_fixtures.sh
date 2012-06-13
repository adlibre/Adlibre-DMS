#!/bin/bash
cd ../src/dms/
./manage.py dumpdata --format=json --indent=4 auth dms_plugins doc_codes djangoplugins > ../../fixtures/initial_data.json
