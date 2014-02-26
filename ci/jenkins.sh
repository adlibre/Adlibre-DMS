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
echo "######################################### Syncdb, migrations ####################################################"
ve/bin/python adlibre_dms/manage.py syncdb --noinput --all
ve/bin/python adlibre_dms/manage.py migrate core --fake
ve/bin/python adlibre_dms/manage.py migrate dms_plugins --fake
echo "########################################## Running code test ####################################################"
ve/bin/python adlibre_dms/manage.py jenkins --verbosity 2