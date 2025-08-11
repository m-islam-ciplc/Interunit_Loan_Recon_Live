from sqlalchemy import create_engine, inspect, text
import pandas as pd
import json
from core.config import MYSQL_USER, MYSQL_PASSWORD, MYSQL_HOST, MYSQL_DB
import re
from core import matching

engine = create_engine(
    f'mysql+pymysql://{MYSQL_USER}:{MYSQL_PASSWORD}@{MYSQL_HOST}/{MYSQL_DB}'
)

def ensure_table_exists(table_name):
    inspector = inspect(engine)
    if table_name not in inspector.get_table_names():
        raise Exception(
            f"Table '{table_name}' does not exist. Please create it manually in MySQL before uploading."
        )

def save_data(df):
    """Save DataFrame to database, with user-friendly duplicate UID error."""
    try:
        ensure_table_exists('tally_data')
        # Replace NaN values with None before saving
        df = df.replace({pd.NA: None, pd.NaT: None})
        df = df.where(pd.notnull(df), None)
        
        # Use chunked insertion for better performance
        chunk_size = 1000
        for i in range(0, len(df), chunk_size):
            chunk = df.iloc[i:i + chunk_size]
            chunk.to_sql('tally_data', engine, if_exists='append', index=False, method='multi')
        
        return True, None
    except Exception as e:
        if 'Duplicate entry' in str(e) and 'uid' in str(e):
            return False, 'Duplicate data: This file (or some records) has already been uploaded.'
        print(f"Error saving data: {e}")
        return False, str(e)

def get_data(filters=None):
    """Get data from database"""
    try:
        ensure_table_exists('tally_data')
        
        # Get column order from database
        with engine.connect() as conn:
            result = conn.execute(text("SHOW COLUMNS FROM tally_data"))
            columns = [row[0] for row in result]
        
        # Build SQL with explicit column order
        column_list = ", ".join(columns)
        sql = f"SELECT {column_list} FROM tally_data"
        params = []
        
        if filters:
            conditions = []
            for key, value in filters.items():
                if value:
                    conditions.append(f"{key} = %s")
                    params.append(value)
            
            if conditions:
                sql += " WHERE " + " AND ".join(conditions)
        
        sql += " ORDER BY Date DESC"
        
        df = pd.read_sql(sql, engine, params=params)
        
        # Convert to records and handle NaN values
        records = df.to_dict('records')
        
        # Replace any remaining NaN values with None for JSON serialization
        for record in records:
            for key, value in record.items():
                if pd.isna(value):
                    record[key] = None
        
        return records
    except Exception as e:
        print(f"Error getting data: {e}")
        return []

def get_filters():
    """Get available filters for the data"""
    engine = create_engine(
        f'mysql+pymysql://{MYSQL_USER}:{MYSQL_PASSWORD}@{MYSQL_HOST}/{MYSQL_DB}'
    )
    
    filters = {}
    
    # Get lenders
    df = pd.read_sql("SELECT DISTINCT lender FROM tally_data WHERE lender IS NOT NULL", engine)
    filters['lenders'] = df['lender'].tolist()
    
    # Get borrowers
    df = pd.read_sql("SELECT DISTINCT borrower FROM tally_data WHERE borrower IS NOT NULL", engine)
    filters['borrowers'] = df['borrower'].tolist()
    
    # Get statement months
    df = pd.read_sql("SELECT DISTINCT statement_month FROM tally_data WHERE statement_month IS NOT NULL", engine)
    filters['statement_months'] = df['statement_month'].tolist()
    
    # Get statement years
    df = pd.read_sql("SELECT DISTINCT statement_year FROM tally_data WHERE statement_year IS NOT NULL", engine)
    filters['statement_years'] = df['statement_year'].tolist()
    
    return filters

def get_unmatched_data():
    """Get all unmatched transactions"""
    try:
        ensure_table_exists('tally_data')
        
        sql = """
        SELECT * FROM tally_data 
        WHERE match_status = 'unmatched' OR match_status IS NULL
        ORDER BY lender ASC, Date DESC
        """
        
        df = pd.read_sql(sql, engine)
        
        # If no data in database, return empty list
        if len(df) == 0:
            print("No data found in database. Please upload files first.")
            return []
        
        # Convert to records and handle NaN values
        records = df.to_dict('records')
        
        # Replace NaN values with None for JSON serialization
        for record in records:
            for key, value in record.items():
                if pd.isna(value):
                    record[key] = None
            
        return records
    except Exception as e:
        print(f"Error getting unmatched data: {e}")
        return []

# Matching functions moved to core/matching.py

def update_matches(matches):
    """Update database with matched records using the hybrid matching system.
    
    Auto-acceptance logic:
    - PO, LC, LOAN_ID, FINAL_SETTLEMENT, and INTERUNIT_LOAN matches are automatically confirmed (high confidence)
    - SALARY and COMMON_TEXT matches require manual review
    
    Stores match information in three columns:
    1. match_method: 'exact' or 'jaccard'
    2. keywords: (deprecated) Simple match text
    3. audit_info: JSON structure containing:
       - match_type: PO, LC, LOAN_ID, SALARY, COMMON_TEXT
       - match_method: exact/jaccard
       - keywords: matched patterns or identifiers
       - jaccard_score: similarity score (when applicable)
    
    This structure provides both quick filtering (match_method)
    and detailed audit information (audit_info JSON)."""
    engine = create_engine(
        f'mysql+pymysql://{MYSQL_USER}:{MYSQL_PASSWORD}@{MYSQL_HOST}/{MYSQL_DB}'
    )
    
    with engine.connect() as conn:
        for i, match in enumerate(matches):
            # Prepare match information and determine auto-acceptance
            # PO, LC, LOAN_ID, FINAL_SETTLEMENT, and INTERUNIT_LOAN matches are auto-accepted due to high confidence
            auto_accept = match['match_type'] in ['PO', 'LC', 'LOAN_ID', 'FINAL_SETTLEMENT', 'INTERUNIT_LOAN']
            
            if match['match_type'] == 'PO':
                match_method = 'reference_match'
            elif match['match_type'] == 'LC':
                match_method = 'reference_match'
            elif match['match_type'] == 'LOAN_ID':
                match_method = 'reference_match'
            elif match['match_type'] == 'SALARY':
                # For salary matches, use the audit trail
                match_method = 'similarity_match'
                jaccard_score = match['audit_trail'].get('jaccard_score', 0)
            elif match['match_type'] == 'FINAL_SETTLEMENT':
                # For final settlement matches, use the audit trail
                match_method = 'reference_match'
            elif match['match_type'] == 'COMMON_TEXT':
                # For COMMON_TEXT matches, use the actual matching text and store in all relevant fields
                common_text = match.get('common_text', '')
                match_method = 'similarity_match'
            elif match['match_type'] == 'INTERUNIT_LOAN':
                # For INTERUNIT_LOAN matches, extract keywords from audit trail
                match_method = 'cross_reference'
            else:
                match_method = 'fallback_match'

            # Store audit information as JSON
            audit_info = {
                'match_type': match['match_type'],
                'match_method': match_method
            }
            
            # Prepare keywords for database storage
            keywords = ''
            if match['match_type'] == 'PO':
                keywords = match.get('po', '')
            elif match['match_type'] == 'LC':
                keywords = match.get('lc', '')
            elif match['match_type'] == 'LOAN_ID':
                keywords = match.get('loan_id', '')
            elif match['match_type'] == 'SALARY':
                keywords = f"person:{match.get('person', '')},period:{match.get('period', '')}"
            elif match['match_type'] == 'FINAL_SETTLEMENT':
                keywords = f"person:{match.get('person', '')}"
            elif match['match_type'] == 'COMMON_TEXT':
                keywords = match.get('common_text', '')
            elif match['match_type'] == 'INTERUNIT_LOAN':
                if 'audit_trail' in match and 'keywords' in match['audit_trail']:
                    keywords_dict = match['audit_trail']['keywords']
                    keywords = f"Lender: {', '.join(keywords_dict.get('lender_interunit_keywords', []))}, Borrower: {', '.join(keywords_dict.get('borrower_interunit_keywords', []))}"
                else:
                    keywords = 'Interunit loan keywords'

            # Add match-specific details to audit trail
            if match['match_type'] == 'PO':
                # Store PO specific audit information
                audit_info['po_number'] = match.get('po', '')
                audit_info['lender_amount'] = match.get('amount', '')
                audit_info['borrower_amount'] = match.get('amount', '')
            elif match['match_type'] == 'LC':
                # Store LC specific audit information
                audit_info['lc_number'] = match.get('lc', '')
                audit_info['lender_amount'] = match.get('amount', '')
                audit_info['borrower_amount'] = match.get('amount', '')
            elif match['match_type'] == 'LOAN_ID':
                # Store LOAN_ID specific audit information
                audit_info['loan_id'] = match.get('loan_id', '')
                audit_info['lender_amount'] = match.get('amount', '')
                audit_info['borrower_amount'] = match.get('amount', '')
            elif match['match_type'] == 'SALARY':
                # Store SALARY specific audit information
                audit_info['person'] = match.get('person', '')
                audit_info['period'] = match.get('period', '')
                audit_info['lender_amount'] = match.get('amount', '')
                audit_info['borrower_amount'] = match.get('amount', '')
                if 'audit_trail' in match and 'jaccard_score' in match['audit_trail']:
                    audit_info['jaccard_score'] = match['audit_trail']['jaccard_score']
            elif match['match_type'] == 'FINAL_SETTLEMENT':
                # Store FINAL_SETTLEMENT specific audit information
                audit_info['person'] = match.get('person', '')
                audit_info['lender_amount'] = match.get('amount', '')
                audit_info['borrower_amount'] = match.get('amount', '')
                if 'audit_trail' in match:
                    audit_info.update(match['audit_trail'])
            elif match['match_type'] == 'COMMON_TEXT':
                # Store COMMON_TEXT specific audit information
                audit_info['common_text'] = common_text
                audit_info['matched_text'] = common_text
                audit_info['matched_phrase'] = common_text
                audit_info['lender_amount'] = match.get('amount', '')
                audit_info['borrower_amount'] = match.get('amount', '')
                if 'audit_trail' in match and 'jaccard_score' in match['audit_trail']:
                    audit_info['jaccard_score'] = match['audit_trail']['jaccard_score']
            elif match['match_type'] == 'INTERUNIT_LOAN':
                # Store INTERUNIT_LOAN specific audit information
                if 'audit_trail' in match:
                    audit_info.update(match['audit_trail'])
                    # Store amount information
                    audit_info['lender_amount'] = match.get('amount', '')
                    audit_info['borrower_amount'] = match.get('amount', '')
                    # Store keywords as string, not object
                    if 'keywords' in match['audit_trail']:
                        keywords_dict = match['audit_trail']['keywords']
                        audit_info['keywords'] = f"Lender: {', '.join(keywords_dict.get('lender_interunit_keywords', []))}, Borrower: {', '.join(keywords_dict.get('borrower_interunit_keywords', []))}"
            elif 'audit_trail' in match and 'jaccard_score' in match['audit_trail']:
                audit_info['jaccard_score'] = match['audit_trail']['jaccard_score']

            # Convert to JSON string (handle Decimal objects)
            def convert_decimal(obj):
                if hasattr(obj, '__str__'):
                    return str(obj)
                return obj
            
            # Convert any Decimal objects to strings
            audit_info_serializable = {}
            for key, value in audit_info.items():
                audit_info_serializable[key] = convert_decimal(value)
            
            audit_json = json.dumps(audit_info_serializable)
            
            # Determine match status: auto-accept PO and LC matches, manual verification for MANUAL_VERIFICATION
            if match['match_type'] == 'MANUAL_VERIFICATION':
                match_status = 'pending_verification'
            else:
                match_status = 'confirmed' if auto_accept else 'matched'
            
            # Update the borrower (Credit) record - point to lender
            result1 = conn.execute(text("""
                UPDATE tally_data 
                SET matched_with = :matched_with, 
                    match_status = :match_status, 
                    match_method = :match_method,
                    audit_info = :audit_info,
                    date_matched = NOW()
                WHERE uid = :borrower_uid
            """), {
                'matched_with': match['lender_uid'],
                'match_status': match_status,
                'match_method': match_method,
                'audit_info': audit_json,
                'borrower_uid': match['borrower_uid']
            })
            
            # Update the lender (Debit) record - point to borrower
            result2 = conn.execute(text("""
                UPDATE tally_data 
                SET matched_with = :matched_with, 
                    match_status = :match_status, 
                    match_method = :match_method,
                    audit_info = :audit_info,
                    date_matched = NOW()
                WHERE uid = :lender_uid
            """), {
                'matched_with': match['borrower_uid'],
                'match_status': match_status,
                'match_method': match_method,
                'audit_info': audit_json,
                'lender_uid': match['lender_uid']
            })
        conn.commit()

def get_matched_data():
    """Get matched transactions with all matching details.
    
    Returns records with hybrid matching information:
    - Basic match details (match_status, matched_with)
    - Match method (exact/jaccard)
    - Full audit trail in audit_info JSON including:
      * Match type (PO, LC, LOAN_ID, SALARY, COMMON_TEXT)
      * Method used (exact/jaccard)
      * Matched patterns/keywords
      * Similarity scores when applicable
    
    Results are ordered by match date descending."""
    engine = create_engine(
        f'mysql+pymysql://{MYSQL_USER}:{MYSQL_PASSWORD}@{MYSQL_HOST}/{MYSQL_DB}'
    )
    
    with engine.connect() as conn:
        result = conn.execute(text("""
            SELECT 
                t1.*,
                t2.lender as matched_lender, 
                t2.borrower as matched_borrower,
                t2.Particulars as matched_particulars, 
                t2.Date as matched_date,
                t2.Debit as matched_Debit, 
                t2.Credit as matched_Credit,
                t2.uid as matched_uid,
                t2.Vch_Type as matched_Vch_Type,
                t2.role as matched_role,
                t1.match_method,
                t1.audit_info as match_audit_info
            FROM tally_data t1
            LEFT JOIN tally_data t2 ON t1.matched_with = t2.uid
            WHERE t1.match_status = 'matched' OR t1.match_status = 'pending_verification'
            ORDER BY t1.date_matched DESC
        """))
        
        records = []
        for row in result:
            record = dict(row._mapping)
            records.append(record)
        
        return records

def get_auto_matched_data():
    """Get only auto-matched transactions (high confidence matches that are automatically accepted).
    
    Returns records with auto-accepted matching information:
    - PO, LC, LOAN_ID, FINAL_SETTLEMENT, and INTERUNIT_LOAN matches
    - These are automatically confirmed due to high confidence
    
    Auto-matches are identified by:
    - match_status = 'confirmed' (automatically accepted)
    - match_method IN ('reference_match', 'cross_reference')
      * reference_match: PO, LC, LOAN_ID, FINAL_SETTLEMENT matches
      * cross_reference: INTERUNIT_LOAN matches
    
    Results are ordered by match date descending."""
    engine = create_engine(
        f'mysql+pymysql://{MYSQL_USER}:{MYSQL_PASSWORD}@{MYSQL_HOST}/{MYSQL_DB}'
    )
    
    with engine.connect() as conn:
        result = conn.execute(text("""
            SELECT 
                t1.*,
                t2.lender as matched_lender, 
                t2.borrower as matched_borrower,
                t2.Particulars as matched_particulars, 
                t2.Date as matched_date,
                t2.Debit as matched_Debit, 
                t2.Credit as matched_Credit,
                t2.uid as matched_uid,
                t2.Vch_Type as matched_Vch_Type,
                t2.role as matched_role,
                t1.match_method,
                t1.audit_info as match_audit_info
            FROM tally_data t1
            LEFT JOIN tally_data t2 ON t1.matched_with = t2.uid
            WHERE t1.match_status = 'confirmed' 
                AND t1.match_method IN ('reference_match', 'cross_reference')
            ORDER BY t1.date_matched DESC
        """))
        
        records = []
        for row in result:
            record = dict(row._mapping)
            records.append(record)
        
        return records

def get_auto_matched_data_by_companies(lender_company, borrower_company, month=None, year=None):
    """Get auto-matched transactions filtered by company names and optionally by statement period.
    
    Only returns high-confidence auto-matches:
    - match_status = 'confirmed' (automatically accepted)
    - match_method IN ('reference_match', 'cross_reference')
      * reference_match: PO, LC, LOAN_ID, FINAL_SETTLEMENT matches
      * cross_reference: INTERUNIT_LOAN matches
    
    Excludes manual matches that require verification (SALARY, COMMON_TEXT)."""
    engine = create_engine(
        f'mysql+pymysql://{MYSQL_USER}:{MYSQL_PASSWORD}@{MYSQL_HOST}/{MYSQL_DB}'
    )
    with engine.connect() as conn:
        # Main query for auto-matched data only
        query = '''
            SELECT 
                t1.*,
                t2.lender as matched_lender, 
                t2.borrower as matched_borrower,
                t2.Particulars as matched_particulars, 
                t2.Date as matched_date,
                t2.Debit as matched_Debit, 
                t2.Credit as matched_Credit,
                t2.uid as matched_uid,
                t2.Vch_Type as matched_Vch_Type,
                t2.role as matched_role
            FROM tally_data t1
            LEFT JOIN tally_data t2 ON t1.matched_with = t2.uid
            WHERE t1.match_status = 'confirmed' 
                AND t1.match_method IN ('reference_match', 'cross_reference')
                AND (
                    (t1.lender = :lender_company AND t1.borrower = :borrower_company)
                    OR (t1.lender = :borrower_company AND t1.borrower = :lender_company)
                )
        '''
        params = {
            'lender_company': lender_company,
            'borrower_company': borrower_company
        }
        if month:
            query += ' AND t1.statement_month = :month'
            params['month'] = month
        if year:
            query += ' AND t1.statement_year = :year'
            params['year'] = year
        query += ' ORDER BY t1.date_matched DESC'
        
        result = conn.execute(text(query), params)
        records = []
        for row in result:
            record = dict(row._mapping)
            records.append(record)
        
        return records

def update_match_status(uid, status, confirmed_by=None):
    """Update match status (accepted/rejected)"""
    try:
        with engine.connect() as conn:
            if status == 'rejected':
                # First, get the matched_with value
                sql_get_matched = """
                SELECT matched_with FROM tally_data WHERE uid = :uid
                """
                result = conn.execute(text(sql_get_matched), {'uid': uid})
                matched_record = result.fetchone()
                
                if matched_record and matched_record[0]:
                    matched_with_uid = matched_record[0]
                    
                    # Reset the main record
                    sql_reset_main = """
                    UPDATE tally_data 
                    SET match_status = 'unmatched', 
                        matched_with = NULL
                    WHERE uid = :uid
                    """
                    conn.execute(text(sql_reset_main), {'uid': uid})
                    
                    # Reset the matched record
                    sql_reset_matched = """
                    UPDATE tally_data 
                    SET match_status = 'unmatched', 
                        matched_with = NULL
                    WHERE uid = :matched_with_uid
                    """
                    conn.execute(text(sql_reset_matched), {'matched_with_uid': matched_with_uid})
                    
                else:
                    # Just reset the main record if no match found
                    sql_reset_main = """
                    UPDATE tally_data 
                    SET match_status = 'unmatched', 
                        matched_with = NULL
                    WHERE uid = :uid
                    """
                    conn.execute(text(sql_reset_main), {'uid': uid})
                
            else:
                # For confirmed status, first get the matched_with value
                sql_get_matched = """
                SELECT matched_with FROM tally_data WHERE uid = :uid
                """
                result = conn.execute(text(sql_get_matched), {'uid': uid})
                matched_record = result.fetchone()
                
                if matched_record and matched_record[0]:
                    matched_with_uid = matched_record[0]
                    
                    # Update the main record
                    sql_update_main = """
                    UPDATE tally_data 
                    SET match_status = :status, 
                        date_matched = NOW()
                    WHERE uid = :uid
                    """
                    conn.execute(text(sql_update_main), {
                        'status': status,
                        'uid': uid
                    })
                    
                    # Update the matched record
                    sql_update_matched = """
                    UPDATE tally_data 
                    SET match_status = :status, 
                        date_matched = NOW()
                    WHERE uid = :matched_with_uid
                    """
                    conn.execute(text(sql_update_matched), {
                        'status': status,
                        'matched_with_uid': matched_with_uid
                    })
                else:
                    # Just update the main record if no match found
                    sql_update_main = """
                    UPDATE tally_data 
                    SET match_status = :status, 
                        date_matched = NOW()
                    WHERE uid = :uid
                    """
                    conn.execute(text(sql_update_main), {
                        'status': status,
                        'uid': uid
                    })
            
            conn.commit()
            return True
            
    except Exception as e:
        print(f"Error updating match status: {e}")
        return False

def get_pending_matches():
    """Get pending matches"""
    engine = create_engine(
        f'mysql+pymysql://{MYSQL_USER}:{MYSQL_PASSWORD}@{MYSQL_HOST}/{MYSQL_DB}'
    )
    
    with engine.connect() as conn:
        result = conn.execute(text("""
            SELECT 
                t1.*, t2.lender as matched_lender, t2.borrower as matched_borrower,
               t2.Particulars as matched_particulars, t2.Date as matched_date,
                t2.Debit as matched_Debit, t2.Credit as matched_Credit,
                t2.uid as matched_uid,
                t2.Vch_Type as matched_Vch_Type, t2.role as matched_role
        FROM tally_data t1
            LEFT JOIN tally_data t2 ON t1.matched_with = t2.uid
            WHERE t1.match_status = 'matched'
            ORDER BY t1.date_matched DESC
        """))
        
        records = []
        for row in result:
            record = dict(row._mapping)
            records.append(record)
        
        return records

def get_confirmed_matches():
    """Get confirmed matches"""
    engine = create_engine(
        f'mysql+pymysql://{MYSQL_USER}:{MYSQL_PASSWORD}@{MYSQL_HOST}/{MYSQL_DB}'
    )
    
    with engine.connect() as conn:
        result = conn.execute(text("""
            SELECT 
                t1.*, t2.lender as matched_lender, t2.borrower as matched_borrower,
               t2.Particulars as matched_particulars, t2.Date as matched_date,
                t2.Debit as matched_Debit, t2.Credit as matched_Credit,
                t2.uid as matched_uid,
                t2.Vch_Type as matched_Vch_Type, t2.role as matched_role
        FROM tally_data t1
            LEFT JOIN tally_data t2 ON t1.matched_with = t2.uid
            WHERE t1.match_status = 'confirmed'
            ORDER BY t1.date_matched DESC
        """))
        
        records = []
        for row in result:
            record = dict(row._mapping)
            records.append(record)
        
        return records

def reset_match_status():
    """Reset all match status columns to clear previous matches"""
    try:
        with engine.connect() as conn:
            # Reset all match-related columns
            reset_query = text("""
                UPDATE tally_data 
                SET match_status = NULL, 
                    matched_with = NULL
            """)
            conn.execute(reset_query)
            conn.commit()
            return True
    except Exception as e:
        print(f"Error resetting match status: {e}")
        return False

def reset_match_status_for_companies(lender_company, borrower_company, month=None, year=None):
    """Reset match status for specific company pair and period"""
    try:
        with engine.connect() as conn:
            query = """
                UPDATE tally_data 
                SET match_status = 'unmatched', 
                    matched_with = NULL,
                    match_method = NULL,
                    audit_info = NULL,
                    date_matched = NULL
                WHERE (
                    (lender = :lender_company AND borrower = :borrower_company)
                    OR (lender = :borrower_company AND borrower = :lender_company)
                )
            """
            params = {
                'lender_company': lender_company,
                'borrower_company': borrower_company
            }
            if month:
                query += ' AND statement_month = :month'
                params['month'] = month
            if year:
                query += ' AND statement_year = :year'
                params['year'] = year
            
            conn.execute(text(query), params)
            conn.commit()
            return True
    except Exception as e:
        print(f"Error resetting match status for companies: {e}")
        return False

def get_column_order():
    """Get the exact column order from the database"""
    try:
        ensure_table_exists('tally_data')
        with engine.connect() as conn:
            result = conn.execute(text("SHOW COLUMNS FROM tally_data"))
            columns = [row[0] for row in result]
        return columns
    except Exception as e:
        print(f"Error getting column order: {e}")
        return [] 

def get_company_pairs():
    """Get available company pairs for reconciliation based on company names and statement periods"""
    engine = create_engine(
        f'mysql+pymysql://{MYSQL_USER}:{MYSQL_PASSWORD}@{MYSQL_HOST}/{MYSQL_DB}'
    )
    
    with engine.connect() as conn:
        # Get all unique company combinations with their statement periods
        # Use LEAST and GREATEST to ensure consistent ordering and avoid duplicates
        result = conn.execute(text("""
            SELECT DISTINCT 
                LEAST(lender, borrower) as company1,
                GREATEST(lender, borrower) as company2,
                statement_month,
                statement_year,
                COUNT(*) as transaction_count
            FROM tally_data 
            WHERE lender IS NOT NULL AND borrower IS NOT NULL
            AND lender != borrower
            GROUP BY LEAST(lender, borrower), GREATEST(lender, borrower), statement_month, statement_year
            HAVING transaction_count >= 2
            ORDER BY statement_year DESC, statement_month DESC, company1, company2
        """))
        
        pairs = []
        for row in result:
            pairs.append({
                'lender_company': row.company1,
                'borrower_company': row.company2,
                'month': row.statement_month,
                'year': row.statement_year,
                'transaction_count': row.transaction_count,
                'description': f"{row.company1} ↔ {row.company2} ({row.statement_month} {row.statement_year})"
            })
        
        return pairs

def detect_company_pairs():
    """Smart scan to detect company pairs based on the pattern in the data"""
    engine = create_engine(
        f'mysql+pymysql://{MYSQL_USER}:{MYSQL_PASSWORD}@{MYSQL_HOST}/{MYSQL_DB}'
    )
    
    with engine.connect() as conn:
        # Get all unique combinations of current company and counterparty
        result = conn.execute(text("""
            SELECT DISTINCT 
                lender as current_company,
                borrower as counterparty,
                statement_month,
                statement_year,
                COUNT(*) as transaction_count
            FROM tally_data 
            WHERE lender IS NOT NULL AND borrower IS NOT NULL
            AND lender != borrower
            GROUP BY lender, borrower, statement_month, statement_year
            HAVING transaction_count >= 1
            ORDER BY statement_year DESC, statement_month DESC, lender, borrower
        """))
        
        # Create a mapping of detected pairs
        detected_pairs = {}
        
        for row in result:
            current_company = row.current_company
            counterparty = row.counterparty
            month = row.statement_month
            year = row.statement_year
            
            # Create a unique key for this combination
            pair_key = f"{current_company}_{counterparty}_{month}_{year}"
            opposite_key = f"{counterparty}_{current_company}_{month}_{year}"
            
            # If we haven't seen this pair or its opposite, add it
            if pair_key not in detected_pairs and opposite_key not in detected_pairs:
                detected_pairs[pair_key] = {
                    'current_company': current_company,
                    'counterparty': counterparty,
                    'month': month,
                    'year': year,
                    'transaction_count': row.transaction_count,
                    'description': f"{current_company} ↔ {counterparty} ({month} {year})",
                    'opposite_pair': {
                        'current_company': counterparty,
                        'counterparty': current_company,
                        'month': month,
                        'year': year,
                        'description': f"{counterparty} ↔ {current_company} ({month} {year})"
                    }
                }
        
        return list(detected_pairs.values())

def get_manual_company_pairs():
    """Get manually defined company pairs from a configuration"""
    from core.config import MANUAL_COMPANY_PAIRS
    
    # Generate opposite pairs automatically
    all_pairs = {}
    for company1, company2 in MANUAL_COMPANY_PAIRS.items():
        if company1 != company2:
            # Add the original pair
            all_pairs[f"{company1}_{company2}"] = (company1, company2)
            # Add the opposite pair
            all_pairs[f"{company2}_{company1}"] = (company2, company1)
    
    engine = create_engine(
        f'mysql+pymysql://{MYSQL_USER}:{MYSQL_PASSWORD}@{MYSQL_HOST}/{MYSQL_DB}'
    )
    
    with engine.connect() as conn:
        pairs = []
        
        # Get all unique statement periods
        result = conn.execute(text("""
            SELECT DISTINCT statement_month, statement_year
            FROM tally_data 
            WHERE statement_month IS NOT NULL AND statement_year IS NOT NULL
            ORDER BY statement_year DESC, statement_month DESC
        """))
        
        for period_row in result:
            month = period_row.statement_month
            year = period_row.statement_year
            
            # For each manual pair, check if both companies exist in this period
            for pair_key, (company1, company2) in all_pairs.items():
                # Check if both companies have data in this period
                count_result = conn.execute(text("""
                    SELECT COUNT(*) as count
                    FROM tally_data 
                    WHERE (lender = :company1 OR borrower = :company1 OR lender = :company2 OR borrower = :company2)
                    AND statement_month = :month AND statement_year = :year
                """), {
                    'company1': company1,
                    'company2': company2,
                    'month': month,
                    'year': year
                })
                
                count = count_result.fetchone()[0]
                if count > 0:
                    pairs.append({
                        'lender_company': company1,
                        'borrower_company': company2,
                        'month': month,
                        'year': year,
                        'transaction_count': count,
                        'description': f"{company1} ↔ {company2} ({month} {year})",
                        'type': 'manual'
                    })
        
        return pairs

def get_unmatched_data_by_companies(lender_company, borrower_company, month=None, year=None):
    """Get unmatched transactions filtered by company names and optionally by statement period"""
    engine = create_engine(
        f'mysql+pymysql://{MYSQL_USER}:{MYSQL_PASSWORD}@{MYSQL_HOST}/{MYSQL_DB}'
    )
    
    with engine.connect() as conn:
        # Build query based on provided parameters
        # Look for transactions where either company appears as lender or borrower
        query = """
            SELECT * FROM tally_data 
            WHERE (match_status = 'unmatched' OR match_status IS NULL)
            AND (
                (lender = :lender_company AND borrower = :borrower_company)
                OR (lender = :borrower_company AND borrower = :lender_company)
            )
        """
        params = {
            'lender_company': lender_company,
            'borrower_company': borrower_company
        }
        
        if month:
            query += " AND statement_month = :month"
            params['month'] = month
        
        if year:
            query += " AND statement_year = :year"
            params['year'] = year
        
        query += " ORDER BY lender ASC, Date DESC"
        
        result = conn.execute(text(query), params)
        
        records = []
        for row in result:
            record = dict(row._mapping)
            records.append(record)
        
        return records

def get_data_by_pair_id(pair_id):
    """Get all data for a specific pair ID"""
    try:
        ensure_table_exists('tally_data')
        
        sql = """
        SELECT * FROM tally_data 
        WHERE pair_id = :pair_id
        ORDER BY Date DESC
        """
        
        df = pd.read_sql(sql, engine, params={'pair_id': pair_id})
        
        # Convert to records and handle NaN values
        records = df.to_dict('records')
        
        # Replace any remaining NaN values with None for JSON serialization
        for record in records:
            for key, value in record.items():
                if pd.isna(value):
                    record[key] = None
        
        return records
    except Exception as e:
        print(f"Error getting data by pair_id: {e}")
        return []

def get_all_pair_ids():
    """Get all unique pair IDs and individual uploads"""
    try:
        ensure_table_exists('tally_data')
        
        # First, try to get file pairs
        pairs_sql = """
        SELECT DISTINCT pair_id, 
               COUNT(*) as record_count,
               MIN(input_date) as upload_date
        FROM tally_data 
        WHERE pair_id IS NOT NULL AND pair_id != ''
        GROUP BY pair_id
        ORDER BY upload_date DESC
        """
        
        df_pairs = pd.read_sql(pairs_sql, engine)
        
        # Also get individual file uploads (records without pair_id but with input_date)
        individual_sql = """
        SELECT 
               CONCAT('individual_', DATE(input_date)) as pair_id,
               COUNT(*) as record_count,
               MIN(input_date) as upload_date
        FROM tally_data 
        WHERE (pair_id IS NULL OR pair_id = '') AND input_date IS NOT NULL
        GROUP BY DATE(input_date)
        ORDER BY upload_date DESC
        """
        
        try:
            df_individual = pd.read_sql(individual_sql, engine)
        except Exception as e:
            print(f"Warning: Could not get individual uploads: {e}")
            df_individual = pd.DataFrame()
        
        # Combine both results
        df_combined = pd.concat([df_pairs, df_individual], ignore_index=True)
        
        pairs = []
        for _, row in df_combined.iterrows():
            pair_data = {
                'pair_id': row['pair_id'],
                'record_count': row['record_count'],
                'upload_date': row['upload_date']
            }
            pairs.append(pair_data)
        
        return pairs
    except Exception as e:
        print(f"Error getting pair IDs: {e}")
        return []

def get_unmatched_data_by_pair_id(pair_id):
    """Get unmatched transactions for a specific pair ID"""
    try:
        ensure_table_exists('tally_data')
        
        sql = """
        SELECT * FROM tally_data 
        WHERE pair_id = :pair_id
        AND (match_status = 'unmatched' OR match_status IS NULL)
        ORDER BY Date DESC
        """
        
        df = pd.read_sql(sql, engine, params={'pair_id': pair_id})
        
        # Convert to records and handle NaN values
        records = df.to_dict('records')
        
        # Replace any remaining NaN values with None for JSON serialization
        for record in records:
            for key, value in record.items():
                if pd.isna(value):
                    record[key] = None
        
        return records
    except Exception as e:
        print(f"Error getting unmatched data by pair_id: {e}")
        return [] 

def get_matched_data_by_companies(lender_company, borrower_company, month=None, year=None):
    """Get matched transactions filtered by company names and optionally by statement period"""
    engine = create_engine(
        f'mysql+pymysql://{MYSQL_USER}:{MYSQL_PASSWORD}@{MYSQL_HOST}/{MYSQL_DB}'
    )
    with engine.connect() as conn:
        # Debug: First check how many total matches exist
        debug_query = '''
            SELECT COUNT(*) as total_matches
            FROM tally_data 
            WHERE (match_status = 'matched' OR match_status = 'confirmed' OR match_status = 'pending_verification')
                AND (
                    (lender = :lender_company AND borrower = :borrower_company)
                    OR (lender = :borrower_company AND borrower = :lender_company)
                )
        '''
        debug_params = {
            'lender_company': lender_company,
            'borrower_company': borrower_company
        }
        if month:
            debug_query += ' AND statement_month = :month'
            debug_params['month'] = month
        if year:
            debug_query += ' AND statement_year = :year'
            debug_params['year'] = year
        
        debug_result = conn.execute(text(debug_query), debug_params)
        total_matches = debug_result.fetchone()[0]
        print(f"DEBUG: Total matches found: {total_matches}")
        
        # Main query
        query = '''
            SELECT 
                t1.*,
                t2.lender as matched_lender, 
                t2.borrower as matched_borrower,
                t2.Particulars as matched_particulars, 
                t2.Date as matched_date,
                t2.Debit as matched_Debit, 
                t2.Credit as matched_Credit,
                t2.uid as matched_uid,
                t2.Vch_Type as matched_Vch_Type,
                t2.role as matched_role
            FROM tally_data t1
            LEFT JOIN tally_data t2 ON t1.matched_with = t2.uid
            WHERE (t1.match_status = 'matched' OR t1.match_status = 'confirmed' OR t1.match_status = 'pending_verification')
                AND (
                    (t1.lender = :lender_company AND t1.borrower = :borrower_company)
                    OR (t1.lender = :borrower_company AND t1.borrower = :lender_company)
                )
        '''
        params = {
            'lender_company': lender_company,
            'borrower_company': borrower_company
        }
        if month:
            query += ' AND t1.statement_month = :month'
            params['month'] = month
        if year:
            query += ' AND t1.statement_year = :year'
            params['year'] = year
        query += ' ORDER BY t1.date_matched DESC'
        result = conn.execute(text(query), params)
        records = []
        for row in result:
            record = dict(row._mapping)
            records.append(record)
        
        print(f"DEBUG: Records returned: {len(records)}")
        
        # Debug: Check for records with NULL matched_with
        null_join_query = '''
            SELECT COUNT(*) as null_joins
            FROM tally_data 
            WHERE (match_status = 'matched' OR match_status = 'confirmed' OR match_status = 'pending_verification')
                AND matched_with IS NULL
                AND (
                    (lender = :lender_company AND borrower = :borrower_company)
                    OR (lender = :borrower_company AND borrower = :lender_company)
                )
        '''
        null_params = {
            'lender_company': lender_company,
            'borrower_company': borrower_company
        }
        if month:
            null_join_query += ' AND statement_month = :month'
            null_params['month'] = month
        if year:
            null_join_query += ' AND statement_year = :year'
            null_params['year'] = year
        
        null_result = conn.execute(text(null_join_query), null_params)
        null_joins = null_result.fetchone()[0]
        print(f"DEBUG: Records with NULL matched_with: {null_joins}")
        
        # Show which specific UIDs have NULL matched_with
        if null_joins > 0:
            null_details_query = '''
                SELECT uid, lender, borrower, statement_month, statement_year, match_status, matched_with
                FROM tally_data 
                WHERE (match_status = 'matched' OR match_status = 'confirmed' OR match_status = 'pending_verification')
                    AND matched_with IS NULL
                    AND (
                        (lender = :lender_company AND borrower = :borrower_company)
                        OR (lender = :borrower_company AND borrower = :lender_company)
                    )
            '''
            if month:
                null_details_query += ' AND statement_month = :month'
            if year:
                null_details_query += ' AND statement_year = :year'
            
            null_details_result = conn.execute(text(null_details_query), null_params)
            for row in null_details_result:
                print(f"DEBUG: NULL matched_with record: {row.uid} - {row.lender} ↔ {row.borrower}")
        
        # Find which match is incomplete (missing one side)
        print("DEBUG: Analyzing match completeness...")
        all_matched_uids = set()
        for record in records:
            if record['uid']:
                all_matched_uids.add(record['uid'])
            if record['matched_uid']:
                all_matched_uids.add(record['matched_uid'])
        
        print(f"DEBUG: Total unique UIDs in matches: {len(all_matched_uids)}")
        print(f"DEBUG: Expected UIDs for 9 matches: 18")
        print(f"DEBUG: Missing UIDs: {18 - len(all_matched_uids)}")
        
        # Find which UID is missing
        all_uids_in_db_query = '''
            SELECT uid FROM tally_data 
            WHERE (match_status = 'matched' OR match_status = 'confirmed' OR match_status = 'pending_verification')
                AND (
                    (lender = :lender_company AND borrower = :borrower_company)
                    OR (lender = :borrower_company AND borrower = :lender_company)
                )
        '''
        if month:
            all_uids_in_db_query += ' AND statement_month = :month'
        if year:
            all_uids_in_db_query += ' AND statement_year = :year'
        
        all_uids_result = conn.execute(text(all_uids_in_db_query), params)
        all_uids_in_db = {row.uid for row in all_uids_result}
        
        missing_uids = all_uids_in_db - all_matched_uids
        if missing_uids:
            print(f"DEBUG: Missing UIDs from matches: {missing_uids}")
        
        # Check for records that exist but don't appear in JOIN results
        print(f"DEBUG: All UIDs in DB: {len(all_uids_in_db)}")
        print(f"DEBUG: UIDs in JOIN results: {len(all_matched_uids)}")
        
        # Find records that have matched_with but the matched record doesn't exist
        orphaned_query = '''
            SELECT t1.uid, t1.matched_with, t1.lender, t1.borrower
            FROM tally_data t1
            LEFT JOIN tally_data t2 ON t1.matched_with = t2.uid
            WHERE (t1.match_status = 'matched' OR t1.match_status = 'confirmed' OR t1.match_status = 'pending_verification')
                AND t1.matched_with IS NOT NULL
                AND t2.uid IS NULL
                AND (
                    (t1.lender = :lender_company AND t1.borrower = :borrower_company)
                    OR (t1.lender = :borrower_company AND t1.borrower = :lender_company)
                )
        '''
        if month:
            orphaned_query += ' AND t1.statement_month = :month'
        if year:
            orphaned_query += ' AND t1.statement_year = :year'
        
        orphaned_result = conn.execute(text(orphaned_query), params)
        orphaned_records = list(orphaned_result)
        if orphaned_records:
            print(f"DEBUG: Orphaned records (matched_with points to non-existent record): {len(orphaned_records)}")
            for record in orphaned_records:
                print(f"DEBUG: Orphaned: {record.uid} -> {record.matched_with}")
        
        return records 

def get_unreconciled_company_pairs():
    """Get company pairs that haven't been reconciled yet (no confirmed/rejected matches)"""
    engine = create_engine(
        f'mysql+pymysql://{MYSQL_USER}:{MYSQL_PASSWORD}@{MYSQL_HOST}/{MYSQL_DB}'
    )
    
    with engine.connect() as conn:
        # Get all unique company combinations with their statement periods
        # Exclude those that already have confirmed or rejected matches
        result = conn.execute(text("""
            SELECT DISTINCT 
                LEAST(lender, borrower) as company1,
                GREATEST(lender, borrower) as company2,
                statement_month,
                statement_year,
                COUNT(*) as transaction_count
            FROM tally_data 
            WHERE lender IS NOT NULL AND borrower IS NOT NULL
            AND lender != borrower
            AND (match_status = 'unmatched' OR match_status IS NULL)
            GROUP BY LEAST(lender, borrower), GREATEST(lender, borrower), statement_month, statement_year
            HAVING transaction_count >= 2
            ORDER BY statement_year ASC, statement_month ASC, company1, company2
        """))
        
        pairs = []
        for row in result:
            pairs.append({
                'lender_company': row.company1,
                'borrower_company': row.company2,
                'month': row.statement_month,
                'year': row.statement_year,
                'transaction_count': row.transaction_count,
                'description': f"{row.company1} ↔ {row.company2} ({row.statement_month} {row.statement_year})"
            })
        
        return pairs 


def get_matched_company_pairs():
    """Get company pairs that have matches (confirmed, pending, or matched status)"""
    engine = create_engine(
        f'mysql+pymysql://{MYSQL_USER}:{MYSQL_PASSWORD}@{MYSQL_HOST}/{MYSQL_DB}'
    )
    
    with engine.connect() as conn:
        # Get all unique company combinations with their statement periods
        # Include those that have matches (matched, confirmed, or pending_verification status)
        result = conn.execute(text("""
            SELECT DISTINCT 
                LEAST(lender, borrower) as company1,
                GREATEST(lender, borrower) as company2,
                statement_month,
                statement_year,
                COUNT(*) as transaction_count
            FROM tally_data 
            WHERE lender IS NOT NULL AND borrower IS NOT NULL
            AND lender != borrower
            AND (match_status = 'matched' OR match_status = 'confirmed' OR match_status = 'pending_verification')
            GROUP BY LEAST(lender, borrower), GREATEST(lender, borrower), statement_month, statement_year
            HAVING transaction_count >= 2
            ORDER BY statement_year DESC, statement_month DESC, company1, company2
        """))
        
        pairs = []
        for row in result:
            pairs.append({
                'lender_company': row.company1,
                'borrower_company': row.company2,
                'month': row.statement_month,
                'year': row.statement_year,
                'transaction_count': row.transaction_count,
                'description': f"{row.company1} ↔ {row.company2} ({row.statement_month} {row.statement_year})"
            })
        
        return pairs


def truncate_table():
    """Truncate the tally_data table - DANGEROUS OPERATION"""
    engine = create_engine(
        f'mysql+pymysql://{MYSQL_USER}:{MYSQL_PASSWORD}@{MYSQL_HOST}/{MYSQL_DB}'
    )
    
    try:
        with engine.connect() as conn:
            # Get count before truncate
            result = conn.execute(text("SELECT COUNT(*) FROM tally_data"))
            count_before = result.fetchone()[0]
            
            # Truncate the table
            conn.execute(text("TRUNCATE TABLE tally_data"))
            conn.commit()
            
            # Get count after truncate
            result = conn.execute(text("SELECT COUNT(*) FROM tally_data"))
            count_after = result.fetchone()[0]
            
            return {
                'success': True,
                'message': f'Table truncated successfully. Removed {count_before} records.',
                'records_removed': count_before,
                'records_remaining': count_after
            }
            
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }

def reset_all_matches():
    """Reset all match status columns - makes all transactions available for matching again"""
    engine = create_engine(
        f'mysql+pymysql://{MYSQL_USER}:{MYSQL_PASSWORD}@{MYSQL_HOST}/{MYSQL_DB}'
    )
    
    try:
        with engine.connect() as conn:
            # Get count of matched records before reset
            result = conn.execute(text("SELECT COUNT(*) FROM tally_data WHERE match_status IS NOT NULL"))
            matched_count = result.fetchone()[0]
            
            # Reset all match-related columns
            conn.execute(text("""
                UPDATE tally_data 
                SET match_status = NULL,
                    matched_with = NULL,
                    match_method = NULL,
                    audit_info = NULL,
                    date_matched = NULL
                WHERE match_status IS NOT NULL
            """))
            conn.commit()
            
            # Get count after reset
            result = conn.execute(text("SELECT COUNT(*) FROM tally_data WHERE match_status IS NOT NULL"))
            remaining_matched = result.fetchone()[0]
            
            return {
                'success': True,
                'message': f'All matches reset successfully. Reset {matched_count} matched records.',
                'records_reset': matched_count,
                'remaining_matched': remaining_matched
            }
            
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        } 