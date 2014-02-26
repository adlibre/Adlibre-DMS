rm -rf ve
rm -rf reports
mkdir reports
virtualenv ve
ve/bin/pip install git+ssh://git@github-Adlibre-DMS/adlibre/Adlibre-DMS.git --upgrade
cp -rf fixtures ve/lib/python2.6/site-packages/fixtures
mkdir ve/lib/python2.6/site-packages/db
mkdir ve/lib/python2.6/site-packages/log/
ve/bin/python adlibre_dms/manage.py syncdb --noinput --all
ve/bin/python adlibre_dms/manage.py migrate core --fake
ve/bin/python adlibre_dms/manage.py migrate dms_plugins --fake
ve/bin/python adlibre_dms/manage.py jenkins --verbosity 2