"""
Module: DMS Utility Functions
Project: Adlibre DMS
Copyright: Adlibre Pty Ltd 2012
License: See LICENSE for license information
"""

def _n(self):
    """
    Return class name and function name of caller.
    User for logging current class and function
    Another approach http://code.activestate.com/recipes/66062-determining-current-function-name/
    """
    from inspect import stack
    class_name = self.__class__.__name__
    function_name = stack()[1][3]
    return "%s.%s" % (class_name, function_name)
