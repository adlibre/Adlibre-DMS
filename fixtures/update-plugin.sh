# these are the commands we used to change plugins package name to djangoplugins

sed -i -e 's@"plugins\.@"djangoplugins\.@g' *.json
#sed -i -e 's@"name": "dms_plugins.pluginpoints@"title": "dms_plugins.pluginpoints@g' *.json

rm -rf *.json-e

#find ../src/ -name '*.py' -exec sed -i -e 's@from plugins@from djangoplugins@g' {} \;
#find ../src/ -name '*.py' -exec sed -i -e 's@import plugins@import djangoplugins@g' {} \;

# also neeed to change:
# from djangoplugins import PluginMount -->  from djangoplugins.point import PluginMount
# and change 'plugins' to 'djangoplugins' in settings.py


#find ../src/ -name '*.py' -exec echo -e "\n" >> {} \;
#find ../src/ -name '*.py-e' -exec rm  {} \;
