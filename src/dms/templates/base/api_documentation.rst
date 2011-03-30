=================
API Documentation
=================

Authentication
--------------

#. Http Basic
#. Oauth

Sending File
------------

-  **URL:** http://www.example.com/api/file/
-  **Method(s):** POST
-  **Parameters:** filename
-  **Returns:** status

You can also send bulk file in compressed format (zip, bz2).

Retrieving File
---------------

-  **URL:** http://www.example.com/api/file/<filename>.<extension>
-  **Method(s):** GET
-  **Parameters:** version, versions
-  **Returns:** file

Query parameters
----------------

-  version
   Get file with version number.

-  versions
   List of available versions.

Rules
-----

List of available rules

-  **URL:** http://www.example.com/api/rules.*format*
-  **Method(s):** GET
-  **Returns:** file

Display detail of a plugin

-  **URL:** http://www.example.com/api/rules/:id.*format*
-  **Method(s):** GET
-  **Returns:** file

Plugins
-------

-  **URL:** http://www.example.com/api/plugins.*format*
-  **Method(s):** GET
-  **Returns:** file
