"""
Tax Code & NI Number Validators — Module 6

Production-grade UK format validators for HMRC compliance.
"""

import re
from compliance.constants import NI_NUMBER_REGEX, VALID_TAX_CODE_SUFFIXES


def validate_tax_code(tax_code: str) -> dict:
    """
    Validate a UK PAYE tax code.

    Valid formats:
    - Standard numeric + suffix: 1257L, 1100L, BR, D0, D1, NT, 0T
    - K codes (negative allowance): K500
    - Scottish codes: S1257L, SBR
    - Welsh codes: C1257L, CBR
    - Week1/Month1 suffix: 1257L W1, 1257L M1

    Returns:
        dict with 'valid' (bool), 'detail' (str), 'parsed' (dict or None)
    """
    if not tax_code or not tax_code.strip():
        return {
            'valid': False,
            'detail': 'Tax code is empty or missing.',
            'parsed': None,
        }

    code = tax_code.strip().upper()

    # Remove W1/M1/X suffix for validation
    week1_month1 = False
    for suffix in [' W1', ' M1', ' X', 'W1', 'M1', 'X']:
        if code.endswith(suffix) and len(code) > len(suffix):
            code = code[:-len(suffix)].strip()
            week1_month1 = True
            break

    # Remove Scottish (S) or Welsh (C) prefix
    country_prefix = ''
    if code.startswith(('S', 'C')) and len(code) > 1 and not code[1:].isalpha():
        country_prefix = code[0]
        code = code[1:]

    # Special codes: BR, D0, D1, NT, 0T
    if code in ['BR', 'D0', 'D1', 'NT', '0T']:
        return {
            'valid': True,
            'detail': f'Valid special tax code: {tax_code}',
            'parsed': {
                'type': 'special',
                'code': code,
                'country_prefix': country_prefix,
                'week1_month1': week1_month1,
            },
        }

    # K codes: K followed by numbers
    if code.startswith('K') and code[1:].isdigit():
        return {
            'valid': True,
            'detail': f'Valid K code (negative allowance): {tax_code}',
            'parsed': {
                'type': 'K',
                'allowance': -int(code[1:]) * 10,
                'country_prefix': country_prefix,
                'week1_month1': week1_month1,
            },
        }

    # Standard codes: numbers + letter suffix (e.g., 1257L)
    match = re.match(r'^(\d+)([A-Z])$', code)
    if match:
        number = int(match.group(1))
        suffix = match.group(2)
        if suffix in ['L', 'M', 'N', 'T']:
            return {
                'valid': True,
                'detail': f'Valid standard tax code: {tax_code}',
                'parsed': {
                    'type': 'standard',
                    'allowance': number * 10,
                    'suffix': suffix,
                    'country_prefix': country_prefix,
                    'week1_month1': week1_month1,
                },
            }

    return {
        'valid': False,
        'detail': f'Invalid tax code format: {tax_code}',
        'parsed': None,
    }


def validate_ni_number(ni_number: str) -> dict:
    """
    Validate a UK National Insurance number.

    Format: 2 letters + 6 digits + 1 letter (A-D)
    Example: QQ123456C

    Excluded prefixes: BG, GB, NK, KN, TN, NT, ZZ
    Second letter cannot be: D, F, I, Q, U, V

    Returns:
        dict with 'valid' (bool) and 'detail' (str)
    """
    if not ni_number or not ni_number.strip():
        return {
            'valid': False,
            'detail': 'National Insurance number is empty or missing.',
        }

    number = ni_number.strip().upper().replace(' ', '')

    # Check format
    if not re.match(NI_NUMBER_REGEX, number):
        return {
            'valid': False,
            'detail': (
                f'Invalid NI number format: {ni_number}. '
                'Expected format: 2 letters + 6 digits + 1 letter (A-D). '
                'Example: QQ123456C'
            ),
        }

    # Check excluded prefixes
    prefix = number[:2]
    excluded_prefixes = ['BG', 'GB', 'NK', 'KN', 'TN', 'NT', 'ZZ']
    if prefix in excluded_prefixes:
        return {
            'valid': False,
            'detail': f'NI number prefix {prefix} is not valid.',
        }

    # Check second letter restrictions
    invalid_second_letters = ['D', 'F', 'I', 'Q', 'U', 'V']
    if number[1] in invalid_second_letters:
        return {
            'valid': False,
            'detail': f'NI number second letter cannot be {number[1]}.',
        }

    return {
        'valid': True,
        'detail': f'Valid National Insurance number.',
    }
