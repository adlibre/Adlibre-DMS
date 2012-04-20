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

Metadata Templates
__________________

List Metadata Templates for Document Type Rule "id" provided

-  **URL:** http://www.example.com/api/mdts/
-  **Method(s):** GET
-  **Parameters:** docrule_id
-  **Returns:** Metadata Template

Delete Metadata Templates with "mdt_id"

-  **URL:** http://www.example.com/api/mdts/
-  **Method(s):** DELETE
-  **Parameters:** mdt_id
-  **Returns:** Status code: 204 (Deleted)

Store Metadata Template

-  **URL:** http://www.example.com/api/mdt/
-  **Method(s):** POST
-  **Parameters:** mdt
-  **Returns:** status

Parameter "mdt" must be JSON for metadata template.
Example MDT:

::

        {
            "docrule_id": "used to assign this to document type rules",
            "description": "<-- description of this metadata template -->",
            "fields": {
                // examples:
                "<-- field number -->":
                     {
                       "type": "string|integer|date",
                       "length": "<--optional-->",
                       "field_name":"<-- field name used in UI -->",
                       "description": "<-- description used in UI -->"
                },
                "1": {
                       "type": "integer",
                       "field_name": "Employee ID",
                       "description": "Unique (Staff) ID of the person"
                },
                "2": {
                       "type": "string",
                       "length": 60,
                       "field_name": "Employee Name",
                       "description": "Name of the person associated with the document"
                }
            },
            // parallel fields mapping
            "parallel": {
                "<-- set id -->": ["<-- first 'field' -->", "<-- second 'field' -->"]
                "1": [ "1", "2"],
            }
        }
