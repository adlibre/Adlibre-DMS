import re
from re_constants import DISALLOWED_PATTERNS, DISALLOWED_CHARS, VALID_SEQUENCE_NUMBER_PATTERNS

def re_regex_is_valid(regex_str=False):
    """
    Validator main.
    validates regex string against applied rules
    """
    if not regex_str:
        return False
    print '1'
    if re_has_disallowed_patterns(regex_str):
        return False
    print '2'
    if not re_has_scopes(regex_str):
        return False
    print '3'
    if not re_equal_scopes(regex_str):
        return False
    print '4'
    if not re_has_one_pattern(regex_str):
        return False
    print '5'
    return True


def re_has_disallowed_patterns(regex_str):
    # Rule
    # checks if string does not have disallowed patterns
    for wrong_pattern in DISALLOWED_PATTERNS:
        try:
            if re.search(wrong_pattern, regex_str):
                return True
        except:
            pass
    for char in DISALLOWED_CHARS:
        if char in regex_str:
            return True
    return False

def re_equal_scopes(regex_str):
    # Rule
    # checking if string has equal {} and [] character count
    a=b=c=d= 0
    for reg_char in regex_str:
        if reg_char[regex_str] == '[': a += 1
        if reg_char[regex_str] == ']': b += 1
        if reg_char[regex_str] == '{': c += 1
        if reg_char[regex_str] == '}': d += 1
    if a==b and c==d:
        return True
    else:
        return False

def re_has_one_pattern(regex_str):
    # Rule
    # checking if regex string has at least one valid pattern
    return re.search('[.-.]', regex_str)


def re_has_scopes(regex_str):
    # Rule
    # checking if regex string has scopes at all
    if not '[' or not ']' in regex_str:
        return False
    if not '[' and not ']' in regex_str:
        return False
    return True


