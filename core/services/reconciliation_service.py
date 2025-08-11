"""
ReconciliationService - Handles reconciliation logic and orchestration.
"""
from typing import Dict, Any, Optional
from core import database
from core import matching


class ReconciliationService:
    """Handles reconciliation logic and orchestration."""
    
    def run_reconciliation(self, lender_company: Optional[str] = None, 
                          borrower_company: Optional[str] = None,
                          month: Optional[str] = None, 
                          year: Optional[str] = None) -> int:
        """Run reconciliation for specified company pair and period."""
        # Get filtered unmatched transactions if company pair is specified
        if lender_company and borrower_company:
            data = database.get_unmatched_data_by_companies(lender_company, borrower_company, month, year)
        else:
            # Get all unmatched transactions if no company pair specified
            data = database.get_unmatched_data()
        
        # Perform matching logic using the matching module
        matches = matching.find_matches(data)
        
        # Update database with matches
        database.update_matches(matches)
        
        return len(matches)
    
    def run_pair_reconciliation(self, pair_id: str) -> int:
        """Run reconciliation for a specific pair ID."""
        # Get unmatched transactions for this pair
        data = database.get_unmatched_data_by_pair_id(pair_id)
        
        # Perform matching logic using the matching module
        matches = matching.find_matches(data)
        
        # Update database with matches
        database.update_matches(matches)
        
        return len(matches)