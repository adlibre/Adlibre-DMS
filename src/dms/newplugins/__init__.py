import pkgutil
from dms.settings import NEW_PLUGIN_DIR

# Automatically import all plugins, so we don't need to add to INSTALLED_APPS
for module in list(pkgutil.iter_modules(["%s" % NEW_PLUGIN_DIR])):
    __import__("newplugins.%s" % module[1], fromlist=[""])

# TODO: FIXME: dont repeat yourself
for module in list(pkgutil.iter_modules(["%s/transfer" % NEW_PLUGIN_DIR])):
    __import__("newplugins.transfer.%s" % module[1], fromlist=[""])