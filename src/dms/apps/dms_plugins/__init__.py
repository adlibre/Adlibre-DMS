import pkgutil

import dms_plugins.workers

for module_loader, name, ispkg in pkgutil.walk_packages(dms_plugins.workers.__path__, dms_plugins.workers.__name__ + "."):
    module_loader.find_module(name).load_module(name)
