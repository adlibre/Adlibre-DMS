"""
Module: Simple Regex string generator
Project: Adlibre DMS
Copyright: Adlibre Pty Ltd 2011
License: See LICENSE for license information
Author: Iurii Garmash
"""

"""
Module built for Adlibre DMS.
Created to generate filename using sequence...
help must be expanded:
....
...
.
..
..

..

.
.
.
.
to run test simply run "python re_gen.py" on this file.
"""

import re

from re_validate import re_regex_is_valid
from re_constants import TEST_REGEXES



def re_generate(regex, last_seq=False):
    """
    Module to generate string sequences according to regex provided.
    Uses only simple syntax.
    e.g.:
    [0-9] = numbers block generated
    [A-z] = letters generated
    [A-Z] = Capital letters block generated
    [a-z] = lowercase letters generated
    {number} = sequence amount
    {from_number,to_number} = sequence possible amount
    """
    if not re_regex_is_valid(regex):
        print 'Error in regex.'
    else:
        print 'OK'

#test suite
for reg in TEST_REGEXES:
    re_generate(reg)