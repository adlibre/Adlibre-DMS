import pkgutil

import pluginpoints

for module_loader, name, ispkg in pkgutil.walk_packages(__path__, __name__ + "."):
     module_loader.find_module(name).load_module(name)