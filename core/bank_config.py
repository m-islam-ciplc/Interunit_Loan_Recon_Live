"""
Bank Configuration Module
Contains bank mappings and configurations for the Interunit Loan Reconciliation system.
Update this file to add new banks or modify existing mappings.
"""

# Bank Code to Full Name Mapping
# Format: 'SHORT_CODE': 'FULL_BANK_NAME'
BANK_MAPPING = {
    # MIDLAND BANK VARIANTS
    'MDBL': 'MIDLAND BANK',
    'MDB': 'MIDLAND BANK',
    'MIDLAND': 'MIDLAND BANK',
    'MIDLAND BANK': 'MIDLAND BANK',
    'MIDLAND BANK PLC': 'MIDLAND BANK',
    'MIDLAND BANK LIMITED': 'MIDLAND BANK',
    
    # BRAC BANK VARIANTS
    'BBL': 'BRAC BANK',
    'BRAC': 'BRAC BANK',
    'BRAC BANK': 'BRAC BANK',
    'BRAC BANK PLC': 'BRAC BANK',
    'BRAC BANK LIMITED': 'BRAC BANK',
    
    # ONE BANK VARIANTS
    'OBL': 'ONE BANK',
    'ONE BANK': 'ONE BANK',
    'ONE BANK PLC': 'ONE BANK',
    'ONE BANK LIMITED': 'ONE BANK',
    
    # EASTERN BANK VARIANTS
    'EBL': 'EASTERN BANK',
    'EASTERN BANK': 'EASTERN BANK',
    'EASTERN BANK PLC': 'EASTERN BANK',
    'EASTERN BANK LIMITED': 'EASTERN BANK',
    
    # DUTCH BANGLA BANK VARIANTS
    'DBL': 'DUTCH BANGLA BANK',
    'DUTCH BANGLA': 'DUTCH BANGLA BANK',
    'DUTCH BANGLA BANK PLC': 'DUTCH BANGLA BANK',
    'DUTCH BANGLA BANK LIMITED': 'DUTCH BANGLA BANK',
    
    # PRIME BANK VARIANTS
    'PBL': 'PRIME BANK',
    'PRIME': 'PRIME BANK',
    'PRIME BANK': 'PRIME BANK',
    'PRIME BANK PLC': 'PRIME BANK',
    'PRIME BANK LIMITED': 'PRIME BANK',
    
    # MUTUAL TRUST BANK VARIANTS
    'MTBL': 'MUTUAL TRUST BANK',
    'MUTUAL TRUST': 'MUTUAL TRUST BANK',
    'MUTUAL TRUST BANK': 'MUTUAL TRUST BANK',
    'MUTUAL TRUST BANK PLC': 'MUTUAL TRUST BANK',
    'MUTUAL TRUST BANK LIMITED': 'MUTUAL TRUST BANK',
    
    # OTHER BANKS
    'NBL': 'NATIONAL BANK',
    'SBL': 'STANDARD BANK',
    'UBL': 'UNITED BANK',
    'CBL': 'CITY BANK'
}

# Bank Account Number Patterns
# These patterns help identify different bank account formats
BANK_ACCOUNT_PATTERNS = {
    'standard': r'([A-Za-z\s-]+[A-Za-z])-?[A-Za-z0-9/-]*(\d{13,16})',
    'hyphenated': r'(\d{3}-\d{10})',
    'fallback': r'(\d{10,})',
    'account_reference': r'#(\d{4,6})'
}

# Account Reference Patterns (for #BBL#121001 format)
ACCOUNT_REFERENCE_PATTERNS = [
    r'([A-Z]{2,4})#(\d{4,6})\b',  # MDBL#11026, OBL#8826 (4-6 digits)
    r'([A-Za-z\s]+)#(\d{4,6})\b',  # Midland Bank#11026
    r'#(\d{4,6})\b',  # #11026 (fallback, 4-6 digits)
]

# Bank-Specific Account Patterns (if needed in the future)
# Format: 'BANK_NAME': {'pattern': regex_pattern, 'description': 'explanation'}
BANK_SPECIFIC_PATTERNS = {
    # Example for future use:
    # 'MIDLAND BANK': {
    #     'pattern': r'MIDLAND\s+BANK[-\s]+(\d{13,16})',
    #     'description': 'Midland Bank specific account format'
    # }
}

def get_bank_mapping():
    """Get the current bank mapping dictionary."""
    return BANK_MAPPING.copy()

def get_bank_name(bank_code):
    """Get normalized bank name from bank code."""
    if not bank_code:
        return None
    return BANK_MAPPING.get(bank_code.upper(), bank_code)

def add_bank_mapping(short_code, full_name):
    """Add a new bank mapping."""
    BANK_MAPPING[short_code.upper()] = full_name.upper()

def update_bank_mapping(short_code, new_full_name):
    """Update an existing bank mapping."""
    if short_code.upper() in BANK_MAPPING:
        BANK_MAPPING[short_code.upper()] = new_full_name.upper()
        return True
    return False

def remove_bank_mapping(short_code):
    """Remove a bank mapping."""
    if short_code.upper() in BANK_MAPPING:
        del BANK_MAPPING[short_code.upper()]
        return True
    return False

def get_account_patterns():
    """Get the current account number patterns."""
    return BANK_ACCOUNT_PATTERNS.copy()

def get_account_reference_patterns():
    """Get the account reference patterns for #BBL#121001 format."""
    return ACCOUNT_REFERENCE_PATTERNS.copy()

def add_bank_specific_pattern(bank_name, pattern, description):
    """Add a bank-specific account pattern."""
    BANK_SPECIFIC_PATTERNS[bank_name.upper()] = {
        'pattern': pattern,
        'description': description
    }

def get_bank_specific_patterns():
    """Get bank-specific account patterns."""
    return BANK_SPECIFIC_PATTERNS.copy()
