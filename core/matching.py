"""
Matching Module - Contains all matching algorithms and logic.
Extracted from core/database.py to separate concerns.
"""
import re
from typing import List, Dict, Any, Optional, Tuple
from core.bank_config import get_bank_name, get_account_reference_patterns


def extract_po(particulars: str) -> Optional[str]:
    """Extract PO number from particulars."""
    if not particulars:
        return None
    
    # Pattern for PO numbers: ABC/PO/123/456 or similar formats
    po_pattern = r'\b[A-Z]{2,4}/PO/\d+/\d+\b'
    try:
        match = re.search(po_pattern, particulars.upper())
        return match.group() if match else None
    except Exception as e:
        print(f"DEBUG: PO regex error: {e} with pattern '{po_pattern}' and text '{particulars}'")
        return None


def extract_lc(particulars: str) -> Optional[str]:
    """Extract LC number from particulars."""
    if not particulars:
        return None
    
    # Pattern for LC numbers: L/C-123/456, LC-123/456, or similar formats
    lc_pattern = r'\b(?:L/C|LC)[-\s]?\d+[/\s]?\d*\b'
    match = re.search(lc_pattern, particulars.upper())
    return match.group() if match else None


def normalize_lc_number(lc_string: str) -> str:
    """Normalize LC number to consistent format for comparison.
    
    Converts both 'L/C-123/456' and 'LC-123/456' to 'LC-123/456'
    """
    if not lc_string:
        return ""
    
    # Remove any extra spaces and normalize to uppercase
    normalized = lc_string.upper().strip()
    
    # Replace 'L/C' with 'LC' for consistent comparison
    normalized = normalized.replace('L/C', 'LC')
    
    return normalized


# Helper: detect the specific Time Loan repayment phrase
def has_time_loan_phrase(particulars: str) -> bool:
    if not particulars:
        return False
    # Accept both variants:
    # - "... Principal & Interest repayment of Time Loan ..."
    # - "... Principal & Interest of Time Loan ..."
    pattern = (
        r"amount\s+being\s+paid\s+as\s*principal\s*&?\s*interest"  # Principal & Interest
        r"(?:\s+repayment)?"                                           # optional 'repayment'
        r"\s+(?:of\s+)?time\s+loan"                                  # 'of Time Loan' or 'Time Loan'
    )
    return re.search(pattern, particulars, flags=re.IGNORECASE) is not None


# Helper: extract normalized loan id like PREFIX-<digits> (e.g., LD-2435445106)
def extract_normalized_loan_id(particulars: str) -> Optional[str]:
    if not particulars:
        return None
    match = re.search(r"\b(?P<prefix>LD|ID|LOAN)[-\s]?(?P<digits>\d+)\b", particulars.upper())
    if not match:
        return None
    prefix = match.group("prefix")
    digits = match.group("digits")
    return f"{prefix}-{digits}"


def extract_normalized_loan_id_after_time_loan_phrase(particulars: str) -> Optional[str]:
    """Extract the first Loan ID that appears AFTER the time loan phrase.
    Normalizes to LD-<digits> for comparison/storage.
    """
    if not particulars:
        return None
    phrase = re.search(
        (
            r"amount\s+being\s+paid\s+as\s*principal\s*&?\s*interest"  # Principal & Interest
            r"(?:\s+repayment)?"                                           # optional 'repayment'
            r"\s+(?:of\s+)?time\s+loan"                                  # 'of Time Loan' or 'Time Loan'
        ),
        particulars,
        flags=re.IGNORECASE,
    )
    if not phrase:
        return None
    start = phrase.end()
    after = particulars[start:]
    m = re.search(r"\b(?:LD|ID|LOAN)[-\s]?(\d+)\b", after.upper())
    if not m:
        return None
    digits = m.group(1)
    return f"LD-{digits}"

def extract_loan_id(particulars: str) -> Optional[str]:
    """Extract Loan ID from particulars."""
    if not particulars:
        return None
    
    # Pattern for Loan IDs: LD123, ID-456, etc.
    loan_pattern = r'\b(?:LD|ID|LOAN)[-\s]?\d+\b'
    match = re.search(loan_pattern, particulars.upper())
    return match.group() if match else None


def extract_account_number(particulars: str) -> Optional[Dict[str, Any]]:
    """Extract account number reference from particulars."""
    if not particulars:
        return None
    
    # Pattern for account number references: #11026, MDBL#11026, OBL#8826, etc.
    # Look for 4-6 digit numbers preceded by # or bank code#
    account_patterns = get_account_reference_patterns()
    
    for i, pattern in enumerate(account_patterns):
        try:
            match = re.search(pattern, particulars.upper())
            if match:
                if len(match.groups()) == 1:
                    # Pattern: #11026
                    account_number = match.group(1)
                    bank_code = None
                else:
                    # Pattern: MDBL#11026 or Midland Bank#11026
                    bank_code = match.group(1).strip()
                    account_number = match.group(2)
                
                # Normalize bank codes using the bank configuration module
                normalized_bank = get_bank_name(bank_code) if bank_code else None
                
                return {
                    'account_number': account_number,
                    'bank_code': bank_code,
                    'normalized_bank': normalized_bank,
                    'full_reference': match.group()
                }
        except Exception as e:
            print(f"DEBUG: Account regex error pattern {i}: {e} with pattern '{pattern}' and text '{particulars}'")
            continue
    
    return None


def calculate_jaccard_similarity(text1: str, text2: str) -> float:
    """Calculate Jaccard similarity between two texts."""
    if not text1 or not text2:
        return 0.0
    
    def preprocess(text: str) -> set:
        # Convert to lowercase and split into words
        words = re.findall(r'\b\w+\b', text.lower())
        # Remove common stop words and short words
        stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by'}
        words = [word for word in words if len(word) > 2 and word not in stop_words]
        return set(words)
    
    set1 = preprocess(text1)
    set2 = preprocess(text2)
    
    if not set1 and not set2:
        return 0.0
    
    intersection = set1.intersection(set2)
    union = set1.union(set2)
    
    return len(intersection) / len(union) if union else 0.0


def extract_final_settlement_details(particulars: str) -> Optional[Dict[str, Any]]:
    """Extract final settlement details from particulars."""
    if not particulars:
        return None
    
    particulars_lower = particulars.lower()
    
    # 1) Lender pattern: "* Amount paid as Inter Unit Loan * (*-ID: *)"
    lender_person_match = re.search(
        r"\(\s*(?P<name>[^()]+?)\s*-\s*ID\s*[:：]\s*(?P<id>\d+)\s*\)",
        particulars,
        flags=re.IGNORECASE,
    ) if ('amount paid as inter unit loan' in particulars_lower) else None
    
    # 2) Borrower pattern: "Payable to *-ID:* * final settlement*"
    borrower_person_match = re.search(
        r"payable\s+to\s+(?P<name>[^\r\n\-]+?)\s*-\s*ID\s*[:：]\s*(?P<id>\d+)",
        particulars,
        flags=re.IGNORECASE | re.DOTALL,
    ) if ('payable to' in particulars_lower and 'final settlement' in particulars_lower) else None
    
    # Extract person details
    person_name = None
    person_id = None
    person_combined = None
    
    if lender_person_match:
        person_name = lender_person_match.group('name').strip()
        person_id = lender_person_match.group('id').strip()
        person_combined = f"{person_name}-ID : {person_id}"
    elif borrower_person_match:
        person_name = borrower_person_match.group('name').strip()
        person_id = borrower_person_match.group('id').strip()
        person_combined = f"{person_name}-ID : {person_id}"
    
    # Only return if we found a person
    if person_combined:
        return {
            'person_name': person_name,
            'person_id': person_id,
            'person_combined': person_combined,
            'is_final_settlement': True
        }
    
    return None


def extract_salary_details(particulars: str) -> Optional[Dict[str, Any]]:
    """Extract salary-related details from particulars."""
    if not particulars:
        return None
    
    particulars_lower = particulars.lower()
    
    # Pre-check for the two explicit patterns provided by requirements
    # 1) Lender pattern: "* Amount paid as Inter Unit Loan * (*-ID: *)"
    lender_person_match = re.search(
        r"\(\s*(?P<name>[^()]+?)\s*-\s*ID\s*[:：]\s*(?P<id>\d+)\s*\)",
        particulars,
        flags=re.IGNORECASE,
    ) if ('amount paid as inter unit loan' in particulars_lower) else None
    
    # 2) Borrower pattern: "Payable to *-ID:* * final settlement*"
    borrower_person_match = re.search(
        r"payable\s+to\s+(?P<name>[^\r\n\-]+?)\s*-\s*ID\s*[:：]\s*(?P<id>\d+)",
        particulars,
        flags=re.IGNORECASE | re.DOTALL,
    ) if ('payable to' in particulars_lower and 'final settlement' in particulars_lower) else None
    
    forced_salary = bool(lender_person_match or borrower_person_match)
    
    # Primary salary keywords found in actual data
    primary_salary_keywords = [
        'salary', 'sal', 'wage', 'payroll', 'remuneration', 'compensation'
    ]
    
    # Secondary keywords (context-dependent)
    secondary_keywords = [
        'monthly', 'month', 'january', 'february', 'march', 'april', 'may', 'june',
        'july', 'august', 'september', 'october', 'november', 'december',
        'jan', 'feb', 'mar', 'apr', 'jun', 'jul', 'aug', 'sep', 'oct', 'nov', 'dec'
    ]
    
    # Check for primary salary keywords first
    # Allow additional real-world triggers to qualify as salary-like
    has_primary_keyword = any(keyword in particulars_lower for keyword in primary_salary_keywords) or (
        'final settlement' in particulars_lower
    )
    
    if not has_primary_keyword:
        return None
    
    # Additional validation: must not contain non-salary indicators
    non_salary_indicators = [
        'payment for', 'purchase of', 'rent', 'electricity', 'transportation', 'marketing',
        'maintenance', 'equipment', 'insurance', 'legal', 'consulting', 'training',
        'travel', 'software', 'security', 'cleaning', 'bank charges', 'interest',
        'loan repayment', 'tax payment', 'bill payment', 'expenses for', 'fees for',
        'vendor payment', 'po no', 'work order', 'invoice', 'challan', 'tds deduction',
        'vds deduction', 'duty', 'taxes', 'port', 'shipping', 'carrying charges',
        'l/c', 'letter of credit', 'margin', 'collateral', 'acceptance commission',
        'retirement value', 'principal', 'time loan', 'usance loan'
    ]
    
    # If any non-salary indicator is present, it's not a salary transaction
    if any(indicator in particulars_lower for indicator in non_salary_indicators) and not forced_salary:
        return None
    
    # Check if this is a salary-related transaction
    is_salary = has_primary_keyword
    
    # Extract person
    # Handle patterns with titles and employee IDs
    person_patterns = [
        # Traditional salary patterns
        r'salary\s+of\s+([A-Za-z\s]+?)(?:\s+for|\s+month|\s+period|$)',
        r'([A-Za-z\s]+?)\s+salary',
        r'payroll\s+for\s+([A-Za-z\s]+?)(?:\s+for|\s+month|\s+period|$)',
        r'([A-Za-z\s]+?)\s+payroll',
        
        # Real-world patterns with titles and employee IDs
        r'\(([A-Za-z]+\.\s+[A-Za-z\s]+?)-ID\s*:\s*\d+\)',  # "(Name-ID : Number)"
        r'([A-Za-z]+\.\s+[A-Za-z\s]+?)-ID\s*:\s*\d+',  # "Name-ID : Number" (without parentheses)
        r'payable\s+to\s+([A-Za-z]+\.\s+[A-Za-z\s]+?)-ID\s*:\s*\d+',  # "Payable to Name-ID:Number"
        r'amount\s+paid\s+to\s+([A-Za-z]+\.\s+[A-Za-z\s]+?)(?:\s*,|\s+for|\s+employee|\s+office|\s+human|\s+resources|\s+administration|\s+final|\s+settlement|\s+employee\s+id|\s*$)',  # "Amount paid to Name"
        r'([A-Za-z]+\.\s+[A-Za-z\s]+?)(?:\s+for|\s+month|\s+period|\s+employee|\s+id|\s*,|\s*$)',  # General pattern for titles
        # Additional pattern for names with titles in parentheses
        r'\(([A-Za-z]+\.\s+[A-Za-z\s]+?)\)',  # "(Name)" - just the name in parentheses
    ]
    
    person_name = None
    person_id = None
    person_combined = None
    
    # Priority: use the explicit lender/borrower patterns first
    if lender_person_match:
        person_name = lender_person_match.group('name').strip()
        person_id = lender_person_match.group('id').strip()
        person_combined = f"{person_name}-ID : {person_id}"
    elif borrower_person_match:
        person_name = borrower_person_match.group('name').strip()
        person_id = borrower_person_match.group('id').strip()
        person_combined = f"{person_name}-ID : {person_id}"
    
    # If not found, fallback to legacy name extraction heuristics
    for pattern in person_patterns:
        if person_combined:
            break
        match = re.search(pattern, particulars_lower)
        if match:
            person_name = match.group(1).strip()
            break
    
    # Fallback: Manual extraction for names in parentheses with employee IDs
    if not person_name:
        # Look for pattern like "(Name-ID : Number)"
        start = particulars_lower.find("(")
        if start != -1:
            end = particulars_lower.find("-id :", start)
            if end != -1:
                # Extract the name part (remove the opening parenthesis)
                name_part = particulars_lower[start+1:end].strip()
                # Check if it looks like a name with title (e.g., "md. name")
                if "." in name_part and len(name_part.split()) >= 2:
                    person_name = name_part
    
    # Extract period (month/year)
    period_patterns = [
        r'(\w+\s+\d{4})',  # "January 2024"
        r'(\d{1,2}/\d{4})',  # "01/2024"
        r'(\d{4}-\d{2})',  # "2024-01"
    ]
    
    period = None
    for pattern in period_patterns:
        match = re.search(pattern, particulars)
        if match:
            period = match.group(1)
            break
    
    # Extract matched keywords for audit trail
    all_keywords = primary_salary_keywords + secondary_keywords
    matched_keywords = [keyword for keyword in all_keywords if keyword in particulars_lower]
    
    return {
        'person_name': person_name,
        'person_id': person_id,
        'person_combined': person_combined,
        'period': period,
        'is_salary': is_salary,
        'matched_keywords': matched_keywords
    }


def extract_common_text(text1: str, text2: str) -> Optional[str]:
    """Extract common text patterns between two strings using continuous phrase matching.

    Focuses on substantial matches (minimum 20 words) to ensure meaningful
    text similarity detection for complex documents like insurance certificates.
    """
    if not text1 or not text2:
        return None

    text1_lower = text1.lower()
    text2_lower = text2.lower()

    # Strategy: Look for continuous phrases (20-50+ words) including numbers/punctuation
    # Extract phrases from both texts
    phrases1 = extract_phrases(text1_lower)
    phrases2 = extract_phrases(text2_lower)

    # Find common phrases
    common_phrases = phrases1.intersection(phrases2)

    if not common_phrases:
        return None

    # Sort phrases by length (longest first) and deduplicate overlapping content
    sorted_phrases = sorted(common_phrases, key=len, reverse=True)

    # Deduplicate: keep only the longest unique phrases (no overlapping content)
    unique_phrases = []
    for phrase in sorted_phrases:
        # Check if this phrase significantly overlaps with any already selected phrase
        is_significantly_overlapping = False
        for selected in unique_phrases:
            # Check for significant overlap (more than 70% similarity)
            if len(phrase) > 0 and len(selected) > 0:
                # Calculate overlap percentage
                if phrase in selected or selected in phrase:
                    is_significantly_overlapping = True
                    break
                # Check for partial overlap by comparing word sets
                words1 = set(phrase.split())
                words2 = set(selected.split())
                if len(words1) > 0 and len(words2) > 0:
                    overlap_ratio = len(words1.intersection(words2)) / max(len(words1), len(words2))
                    if overlap_ratio > 0.7:  # More than 70% overlap
                        is_significantly_overlapping = True
                        break

        if not is_significantly_overlapping:
            unique_phrases.append(phrase)
            # Limit to top 2 unique phrases to keep output focused
            if len(unique_phrases) >= 2:
                break

    if unique_phrases:
        # Return common text with word count in clean format
        result = []
        for phrase in unique_phrases:
            word_count = len(phrase.split())
            # Show up to 50 words, add (CONT...) if longer
            words = phrase.split()
            if len(words) > 50:
                display_phrase = ' '.join(words[:50]) + ' (CONT...)'
            else:
                display_phrase = phrase
            result.append(f"{word_count} words: {display_phrase}")

        return ' | '.join(result)

    return None


def extract_phrases(text: str, min_words: int = 20, max_words: int = 50) -> set:
    """Extract phrases of 20-50 words from text, including numbers and punctuation.
    
    This function focuses only on long continuous text matches that include
    mixed text and numbers, such as insurance certificates, vehicle details, etc.
    Minimum 20 words ensures meaningful, substantial matches.
    """
    # Split text into tokens (words, numbers, punctuation)
    # Enhanced pattern to better capture mixed alphanumeric sequences
    tokens = re.findall(r'\b\w+\b|\d+(?:\.\d+)?|\d+[/\-]\d+|[A-Za-z0-9]+[/\-][A-Za-z0-9]+|[A-Za-z0-9]+(?:\-[A-Za-z0-9]+)*|[^\w\s]', text)
    phrases = set()
    
    for i in range(len(tokens) - min_words + 1):
        for length in range(min_words, min(max_words + 1, len(tokens) - i + 1)):
            phrase = ' '.join(tokens[i:i + length])
            if len(phrase) >= 50:  # Minimum phrase length (increased for 20+ words)
                phrases.add(phrase)
    
    return phrases





def find_matches(data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Match transactions using a hybrid approach combining exact and Jaccard similarity matching.
    
    Matching Strategy:
    1. Amount match (Debit == Credit) as base requirement
    2. Document reference matches (exact matching):
       - PO numbers (e.g., ABC/PO/123/456)
       - LC numbers (e.g., L/C-123/456)
       - Loan IDs (e.g., LD123, ID-456)
    3. Salary payment matches (hybrid):
       - Exact match: person name and period
       - Jaccard similarity: description comparison (threshold: 0.3)
    4. Common text pattern match (fallback)
       - Uses Jaccard similarity for general descriptions
    
    The hybrid approach ensures:
    - High accuracy for structured identifiers (PO, LC, Loan ID)
    - Flexibility for variations in descriptions (Salary, General text)
    - Complete audit trail in audit_info JSON
    """
    if not data:
        print("No data to match")
        return []
    
    lenders = [r for r in data if r.get('Debit') and r['Debit'] > 0]
    borrowers = [r for r in data if r.get('Credit') and r['Credit'] > 0]
    
    matches = []
    # Track which records have already been matched to prevent duplicates
    matched_lenders = set()
    matched_borrowers = set()
    
    for lender in lenders:
        # Skip if this lender is already matched
        if lender['uid'] in matched_lenders:
            continue
            
        lender_po = extract_po(lender.get('Particulars', ''))
        lender_lc = extract_lc(lender.get('Particulars', ''))
        lender_loan_id = extract_loan_id(lender.get('Particulars', ''))
        lender_account = extract_account_number(lender.get('Particulars', ''))
        lender_salary = extract_salary_details(lender.get('Particulars', ''))
        

        
        for borrower in borrowers:
            # Skip if this borrower is already matched
            if borrower['uid'] in matched_borrowers:
                continue
                
            if float(lender['Debit']) == float(borrower['Credit']):
                borrower_po = extract_po(borrower.get('Particulars', ''))
                borrower_lc = extract_lc(borrower.get('Particulars', ''))
                borrower_loan_id = extract_loan_id(borrower.get('Particulars', ''))
                borrower_account = extract_account_number(borrower.get('Particulars', ''))
                borrower_salary = extract_salary_details(borrower.get('Particulars', ''))
                
                # PO match
                if lender_po and borrower_po and lender_po == borrower_po:
                    matches.append({
                        'lender_uid': lender['uid'],
                        'borrower_uid': borrower['uid'],
                        'amount': lender['Debit'],
                        'match_type': 'PO',
                        'po': lender_po
                    })
                    # Mark both records as matched
                    matched_lenders.add(lender['uid'])
                    matched_borrowers.add(borrower['uid'])
                    break
                    
                # Final Settlement match
                lender_final_settlement = extract_final_settlement_details(lender.get('Particulars', ''))
                borrower_final_settlement = extract_final_settlement_details(borrower.get('Particulars', ''))
                
                if lender_final_settlement and borrower_final_settlement:
                    # Check if both sides have the same person
                    if lender_final_settlement['person_name'] == borrower_final_settlement['person_name']:
                        matches.append({
                            'lender_uid': lender['uid'],
                            'borrower_uid': borrower['uid'],
                            'amount': lender['Debit'],
                            'match_type': 'FINAL_SETTLEMENT',
                            'person': lender_final_settlement['person_combined'],
                            'audit_trail': {
                                'match_reason': 'Final settlement match',
                                'lender_person': lender_final_settlement['person_combined'],
                                'borrower_person': borrower_final_settlement['person_combined'],
                                'person_name': lender_final_settlement['person_name'],
                                'person_id': lender_final_settlement['person_id']
                            }
                    })
                    # Mark both records as matched
                    matched_lenders.add(lender['uid'])
                    matched_borrowers.add(borrower['uid'])
                    break
                    
                # Salary payment match with both exact and Jaccard matching
                lender_text = lender.get('Particulars', '')
                borrower_text = borrower.get('Particulars', '')
                jaccard_score = calculate_jaccard_similarity(lender_text, borrower_text)
                
                if lender_salary and borrower_salary:
                    # Exact keyword matching
                    exact_match = (lender_salary['person_name'] == borrower_salary['person_name'] and 
                                 lender_salary['period'] == borrower_salary['period'] and
                                 lender_salary['is_salary'] and borrower_salary['is_salary'])
                    
                    # Jaccard similarity threshold for salary descriptions
                    jaccard_threshold = 0.3  # Can be adjusted based on requirements
                    
                    if exact_match or jaccard_score >= jaccard_threshold:
                        # Combine matched keywords and similarity score for audit trail
                        audit_keywords = {
                            'lender_keywords': lender_salary['matched_keywords'] if lender_salary else [],
                            'borrower_keywords': borrower_salary['matched_keywords'] if borrower_salary else [],
                            'jaccard_score': round(jaccard_score, 3),
                            'match_method': 'exact' if exact_match else 'jaccard'
                        }
                        
                        matches.append({
                            'lender_uid': lender['uid'],
                            'borrower_uid': borrower['uid'],
                            'amount': lender['Debit'],
                            'match_type': 'SALARY',
                            'person': (
                                lender_salary.get('person_combined')
                                if lender_salary and lender_salary.get('person_combined')
                                else lender_salary.get('person_name') if lender_salary else None
                            ),
                            'period': lender_salary['period'] if lender_salary else None,
                            'audit_trail': audit_keywords
                        })
                        # Mark both records as matched
                        matched_lenders.add(lender['uid'])
                        matched_borrowers.add(borrower['uid'])
                        break

                
                # LC match
                if lender_lc and borrower_lc and normalize_lc_number(lender_lc) == normalize_lc_number(borrower_lc):
                    matches.append({
                        'lender_uid': lender['uid'],
                        'borrower_uid': borrower['uid'],
                        'amount': lender['Debit'],
                        'match_type': 'LC',
                        'lc': lender_lc
                    })
                    # Mark both records as matched
                    matched_lenders.add(lender['uid'])
                    matched_borrowers.add(borrower['uid'])
                    break
                
                # Interunit Loan match (auto-confirmed, runs after PO and LC)
                # Two-way cross-reference matching for interunit loan transactions
                lender_particulars = lender.get('Particulars', '')
                borrower_particulars = borrower.get('Particulars', '')
                
                # Check for interunit loan keywords (more flexible matching)
                lender_lower = lender_particulars.lower()
                borrower_lower = borrower_particulars.lower()
                
                is_lender_interunit = (
                    'amount paid as interunit loan' in lender_lower or 
                    'interunit fund transfer' in lender_lower or
                    'inter unit fund transfer' in lender_lower or
                    'interunit loan' in lender_lower
                )
                is_borrower_interunit = (
                    'amount received as interunit loan' in borrower_lower or 
                    'interunit fund transfer' in borrower_lower or
                    'inter unit fund transfer' in borrower_lower or
                    'interunit loan' in borrower_lower
                )
                
                if (is_lender_interunit and is_borrower_interunit):
                    # Extract account numbers from both narrations using multiple patterns
                    lender_account_match = None
                    borrower_account_match = None
                    
                    # Pattern 1: For lender - extract full account number after bank name
                    lender_account_match = re.search(r'([A-Za-z\s-]+[A-Za-z])-?[A-Za-z0-9/-]*(\d{13,16})', lender_particulars)
                    # Pattern 2: For borrower - extract hyphenated account number
                    borrower_account_match = re.search(r'([A-Za-z\s-]+[A-Za-z])-?[A-Za-z0-9/-]*(\d{3}-\d{10})', borrower_particulars)
                    
                    # Pattern 3: Fallback for any account number format
                    if not lender_account_match:
                        lender_account_match = re.search(r'([A-Za-z\s-]+[A-Za-z])-?[A-Za-z0-9/-]*(\d{10,})', lender_particulars)
                    if not borrower_account_match:
                        borrower_account_match = re.search(r'([A-Za-z\s-]+[A-Za-z])-?[A-Za-z0-9/-]*(\d{10,})', borrower_particulars)
                    
                    # If still not found, try more generic patterns
                    if not lender_account_match:
                        # Try to extract from any pattern with 13-16 digits
                        lender_account_match = re.search(r'(\d{13,16})', lender_particulars)
                    if not borrower_account_match:
                        # Try to extract from any pattern with hyphenated account
                        borrower_account_match = re.search(r'(\d{3}-\d{10})', borrower_particulars)
                    
                    if lender_account_match and borrower_account_match:
                        # Extract last 4-5 digits from both account numbers
                        if len(lender_account_match.groups()) >= 2:
                            lender_account_full = lender_account_match.group(2)
                        else:
                            lender_account_full = lender_account_match.group(1)
                        
                        if len(borrower_account_match.groups()) >= 2:
                            borrower_account_full = borrower_account_match.group(2)
                        else:
                            borrower_account_full = borrower_account_match.group(1)
                        
                        lender_last_digits = lender_account_full[-5:] if len(lender_account_full) >= 5 else lender_account_full[-4:]
                        borrower_last_digits = borrower_account_full[-5:] if len(borrower_account_full) >= 5 else borrower_account_full[-4:]
                        
                        # Cross-reference 1: Lender → Borrower
                        # Look for lender's last digits in borrower's narration
                        cross_ref_1_found = lender_last_digits in borrower_particulars
                        
                        # Cross-reference 2: Borrower → Lender
                        # Look for borrower's last digits in lender's narration
                        cross_ref_2_found = borrower_last_digits in lender_particulars
                        
                        # Alternative: Look for the shortened references in the narrations
                        if not cross_ref_1_found:
                            # Look for any 4-5 digit number followed by # in borrower narration
                            borrower_short_ref = re.search(r'#(\d{4,5})', borrower_particulars)
                            if borrower_short_ref:
                                cross_ref_1_found = borrower_short_ref.group(1) in lender_last_digits
                        
                        if not cross_ref_2_found:
                            # Look for any 4-5 digit number followed by # in lender narration
                            lender_short_ref = re.search(r'#(\d{4,5})', lender_particulars)
                            if lender_short_ref:
                                cross_ref_2_found = lender_short_ref.group(1) in borrower_last_digits
                        
                        # Both cross-references must be found
                        if cross_ref_1_found and cross_ref_2_found:
                            matches.append({
                                'lender_uid': lender['uid'],
                                'borrower_uid': borrower['uid'],
                                'amount': lender['Debit'],
                                'match_type': 'INTERUNIT_LOAN',
                                'lender_account': lender_account_full,
                                'borrower_account': borrower_account_full,
                                'lender_last_digits': lender_last_digits,
                                'borrower_last_digits': borrower_last_digits,
                                'audit_trail': {
                                    'lender_reference': f"{lender_account_match.group(1) if len(lender_account_match.groups()) >= 1 else 'Unknown'}-{lender_account_full}",
                                    'borrower_reference': f"{borrower_account_match.group(1) if len(borrower_account_match.groups()) >= 1 else 'Unknown'}-{borrower_account_full}",
                                    'match_reason': f"Interunit loan cross-reference match: {lender_last_digits} ↔ {borrower_last_digits}",
                                    'keywords': {
                                        'lender_interunit_keywords': ['amount paid as interunit loan', 'interunit fund transfer'],
                                        'borrower_interunit_keywords': ['amount received as interunit loan', 'interunit fund transfer'],
                                        'account_patterns': ['generic bank name + account number', 'hyphenated account format'],
                                        'cross_reference_patterns': ['#\\d{4,5}']
                                    },
                                    'validation': {
                                        'lender_interunit': is_lender_interunit,
                                        'borrower_interunit': is_borrower_interunit,
                                        'cross_reference_1': cross_ref_1_found,
                                        'cross_reference_2': cross_ref_2_found,
                                        'interunit_loan_transaction': True
                                    }
                                }
                            })
                            # Mark both records as matched
                            matched_lenders.add(lender['uid'])
                            matched_borrowers.add(borrower['uid'])
                            break
                    
                
                # Loan ID match (redefined condition):
                # If both narrations contain the Time Loan phrase and share the same Loan ID AFTER the phrase
                lender_text_full = lender.get('Particulars', '')
                borrower_text_full = borrower.get('Particulars', '')
                if has_time_loan_phrase(lender_text_full) and has_time_loan_phrase(borrower_text_full):
                    lender_after_id = extract_normalized_loan_id_after_time_loan_phrase(lender_text_full)
                    borrower_after_id = extract_normalized_loan_id_after_time_loan_phrase(borrower_text_full)
                    if lender_after_id and borrower_after_id and lender_after_id == borrower_after_id:
                        matches.append({
                            'lender_uid': lender['uid'],
                            'borrower_uid': borrower['uid'],
                            'amount': lender['Debit'],
                            'match_type': 'LOAN_ID',
                            'loan_id': lender_after_id,
                            'audit_trail': {
                                'match_reason': 'Time Loan phrase + matching Loan ID after phrase',
                                'phrase_detected': True
                            }
                        })
                        # Mark both records as matched
                        matched_lenders.add(lender['uid'])
                        matched_borrowers.add(borrower['uid'])
                        break
                
                # Loan ID match (generic exact token equality)
                if lender_loan_id and borrower_loan_id and lender_loan_id == borrower_loan_id:
                    matches.append({
                        'lender_uid': lender['uid'],
                        'borrower_uid': borrower['uid'],
                        'amount': lender['Debit'],
                        'match_type': 'LOAN_ID',
                        'loan_id': lender_loan_id
                    })
                    # Mark both records as matched
                    matched_lenders.add(lender['uid'])
                    matched_borrowers.add(borrower['uid'])
                    break
                
                # Final Settlement match
                final_settlement_match = extract_final_settlement_details(lender.get('Particulars', ''))
                if final_settlement_match:
                    matches.append({
                        'lender_uid': lender['uid'],
                        'borrower_uid': borrower['uid'],
                        'amount': lender['Debit'],
                        'match_type': 'FINAL_SETTLEMENT',
                        'person': final_settlement_match['person_combined'],
                        'audit_trail': {
                            'match_reason': 'Final settlement match',
                            'person_name': final_settlement_match['person_name'],
                            'person_id': final_settlement_match['person_id'],
                            'is_final_settlement': final_settlement_match['is_final_settlement']
                        }
                    })
                    # Mark both records as matched
                    matched_lenders.add(lender['uid'])
                    matched_borrowers.add(borrower['uid'])
                    break
                
                # Manual verification match (lowest priority - requires user verification)
                # This matches records where debit, credit, and entered_by are exactly the same
                lender_entered_by = lender.get('entered_by', '')
                borrower_entered_by = borrower.get('entered_by', '')
                
                if (lender_entered_by and borrower_entered_by and 
                    lender_entered_by == borrower_entered_by):
                    matches.append({
                        'lender_uid': lender['uid'],
                        'borrower_uid': borrower['uid'],
                        'amount': lender['Debit'],
                        'match_type': 'MANUAL_VERIFICATION',
                        'entered_by': lender_entered_by,
                        'audit_trail': {
                            'match_reason': 'Exact match on debit, credit, and entered_by fields',
                            'requires_verification': True
                        }
                    })
                    # Mark both records as matched
                    matched_lenders.add(lender['uid'])
                    matched_borrowers.add(borrower['uid'])
                    break
                
                # Common text pattern match (fallback - only if no other matches found)
                common_text = extract_common_text(
                    lender.get('Particulars', ''),
                    borrower.get('Particulars', '')
                )
                if common_text and isinstance(common_text, str) and common_text.strip():
                    # Calculate Jaccard score for the overall texts
                    text_similarity = calculate_jaccard_similarity(
                        lender.get('Particulars', ''),
                        borrower.get('Particulars', '')
                    )
                    matches.append({
                        'lender_uid': lender['uid'],
                        'borrower_uid': borrower['uid'],
                        'amount': lender['Debit'],
                        'match_type': 'COMMON_TEXT',
                        'common_text': common_text.strip(),
                        'audit_trail': {
                            'jaccard_score': round(text_similarity, 3),
                            'matched_phrase': common_text.strip()  # Store the actual matching phrase
                        }
                    })
                    # Mark both records as matched
                    matched_lenders.add(lender['uid'])
                    matched_borrowers.add(borrower['uid'])
                    break
    
    return matches 
