"""
Reconciliation Routes - Handles all matching and reconciliation endpoints.
"""
from flask import Blueprint, request, jsonify
from core.services.reconciliation_service import ReconciliationService
from core import database

reconciliation_bp = Blueprint('reconciliation', __name__)

@reconciliation_bp.route('/reconcile', methods=['POST'])
def reconcile_transactions():
    """Run reconciliation on all data - REFACTORED to use ReconciliationService"""
    try:
        # Get parameters from request
        data = request.get_json()
        lender_company = data.get('lender_company')
        borrower_company = data.get('borrower_company')
        month = data.get('month')
        year = data.get('year')
        
        # Use ReconciliationService for reconciliation
        reconciliation_service = ReconciliationService()
        matches_found = reconciliation_service.run_reconciliation(
            lender_company, borrower_company, month, year
        )
        
        return jsonify({
            'message': 'Reconciliation complete.',
            'matches_found': matches_found
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@reconciliation_bp.route('/reconcile-pair/<pair_id>', methods=['POST'])
def reconcile_pair(pair_id):
    """Reconcile transactions for a specific pair - REFACTORED to use ReconciliationService"""
    try:
        # Use ReconciliationService for pair reconciliation
        reconciliation_service = ReconciliationService()
        matches_found = reconciliation_service.run_pair_reconciliation(pair_id)
        
        return jsonify({
            'message': f'Reconciliation complete for pair {pair_id}.',
            'matches_found': matches_found
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@reconciliation_bp.route('/matches', methods=['GET'])
def get_matches():
    """Get matched data with optional filtering"""
    try:
        # Get filter parameters
        lender_company = request.args.get('lender_company')
        borrower_company = request.args.get('borrower_company')
        month = request.args.get('month')
        year = request.args.get('year')
        
        # Apply filters if provided
        if lender_company and borrower_company:
            data = database.get_matched_data_by_companies(lender_company, borrower_company, month, year)
        else:
            data = database.get_matched_data()
        
        return jsonify({'matches': data})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@reconciliation_bp.route('/pending-matches', methods=['GET'])
def get_pending_matches():
    """Get pending matches"""
    try:
        data = database.get_pending_matches()
        return jsonify({'pending_matches': data})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@reconciliation_bp.route('/confirmed-matches', methods=['GET'])
def get_confirmed_matches():
    """Get confirmed matches"""
    try:
        data = database.get_confirmed_matches()
        return jsonify({'confirmed_matches': data})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@reconciliation_bp.route('/accept-match', methods=['POST'])
def accept_match():
    """Accept a match"""
    try:
        data = request.get_json()
        uid = data.get('uid')
        confirmed_by = data.get('confirmed_by', 'user')
        
        if not uid:
            return jsonify({'error': 'UID is required'}), 400
        
        success = database.update_match_status(uid, 'confirmed', confirmed_by)
        
        if success:
            return jsonify({'message': 'Match accepted successfully'})
        else:
            return jsonify({'error': 'Failed to accept match'}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@reconciliation_bp.route('/reject-match', methods=['POST'])
def reject_match():
    """Reject a match"""
    try:
        data = request.get_json()
        uid = data.get('uid')
        confirmed_by = data.get('confirmed_by', 'user')
        
        if not uid:
            return jsonify({'error': 'UID is required'}), 400
        
        success = database.update_match_status(uid, 'rejected', confirmed_by)
        
        if success:
            return jsonify({'message': 'Match rejected successfully'})
        else:
            return jsonify({'error': 'Failed to reject match'}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500 