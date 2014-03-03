#!/bin/sh
echo "#############################   Cleanup old virtualenvironment and reports ######################################"
rm -rf ve
rm -rf reports
mkdir reports

echo "########################################## Creating new VE ######################################################"
virtualenv ve > create_virtualenv.log
ve/bin/pip install git+ssh://git@github-Adlibre-DMS/adlibre/Adlibre-DMS.git --upgrade > populate_virtualenv.log

echo "########################################### Linking stuff #######################################################"
cp -rf fixtures ve/lib/python2.6/site-packages/fixtures
mkdir ve/lib/python2.6/site-packages/db
mkdir ve/lib/python2.6/site-packages/log/

echo "##################################### Syncdb, migrations, fixtures ##############################################"
ve/bin/python adlibre_dms/manage.py syncdb --noinput --all
ve/bin/python adlibre_dms/manage.py migrate core --fake
ve/bin/python adlibre_dms/manage.py migrate dms_plugins --fake
ve/bin/python adlibre_dms/manage.py loaddata ve/lib/python2.6/site-packages/fixtures/initial_datas.json
ve/bin/python adlibre_dms/manage.py loaddata ve/lib/python2.6/site-packages/fixtures/core.json
ve/bin/python adlibre_dms/manage.py loaddata ve/lib/python2.6/site-packages/fixtures/djangoplugins.json
ve/bin/python adlibre_dms/manage.py loaddata ve/lib/python2.6/site-packages/fixtures/dms_plugins.json

echo "########################################## Running code test ####################################################"
# Change into this to make detailed tests report
# ve/bin/python adlibre_dms/manage.py jenkins --verbosity 2
ve/bin/python adlibre_dms/manage.py jenkins