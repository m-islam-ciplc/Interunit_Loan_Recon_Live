"""
Data Routes - Handles all data retrieval and filtering endpoints.
"""
from flask import Blueprint, request, jsonify
from core import database

data_bp = Blueprint('data', __name__)

@data_bp.route('/data', methods=['GET'])
def get_data():
    """Get data with optional filtering"""
    try:
        filters = {
            'lender': request.args.get('lender'),
            'borrower': request.args.get('borrower'),
            'statement_month': request.args.get('statement_month'),
            'statement_year': request.args.get('statement_year'),
            'vch_type': request.args.get('vch_type'),
            'entered_by': request.args.get('entered_by')
        }
        
        # Remove None values
        filters = {k: v for k, v in filters.items() if v is not None}
        
        data = database.get_data(filters)
        return jsonify({'data': data})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@data_bp.route('/filters', methods=['GET'])
def get_filters():
    """Get available filter options"""
    try:
        filters = database.get_filters()
        return jsonify(filters)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@data_bp.route('/unmatched', methods=['GET'])
def get_unmatched_data():
    """Get unmatched data with optional filtering"""
    try:
        # Get filter parameters
        lender_company = request.args.get('lender_company')
        borrower_company = request.args.get('borrower_company')
        month = request.args.get('month')
        year = request.args.get('year')
        
        # Apply filters if provided
        if lender_company and borrower_company:
            data = database.get_unmatched_data_by_companies(lender_company, borrower_company, month, year)
        else:
            data = database.get_unmatched_data()
        
        return jsonify({'unmatched': data})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@data_bp.route('/pair/<pair_id>/unmatched', methods=['GET'])
def get_pair_unmatched_data(pair_id):
    """Get unmatched data for a specific pair"""
    try:
        data = database.get_unmatched_data_by_pair_id(pair_id)
        return jsonify({'unmatched': data, 'pair_id': pair_id})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@data_bp.route('/pair/<pair_id>/data', methods=['GET'])
def get_pair_data(pair_id):
    """Get data for a specific pair"""
    try:
        data = database.get_data_by_pair_id(pair_id)
        return jsonify({'data': data, 'pair_id': pair_id})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@data_bp.route('/detected-pairs', methods=['GET'])
def get_detected_pairs():
    """Get detected company pairs"""
    try:
        pairs = database.detect_company_pairs()
        return jsonify({'pairs': pairs})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@data_bp.route('/manual-pairs', methods=['GET'])
def get_manual_pairs():
    """Get manual company pairs"""
    try:
        pairs = database.get_manual_company_pairs()
        return jsonify({'pairs': pairs})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@data_bp.route('/pairs', methods=['GET'])
def get_all_pairs():
    """Get all upload pairs with pair IDs"""
    try:
        pairs = database.get_all_pair_ids()
        return jsonify({'pairs': pairs})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@data_bp.route('/unreconciled-pairs', methods=['GET'])
def get_unreconciled_pairs():
    """Get unreconciled company pairs"""
    try:
        pairs = database.get_unreconciled_company_pairs()
        return jsonify({'pairs': pairs})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@data_bp.route('/matched-pairs', methods=['GET'])
def get_matched_pairs():
    """Get matched company pairs"""
    try:
        pairs = database.get_matched_company_pairs()
        return jsonify({'pairs': pairs})
    except Exception as e:
        return jsonify({'error': str(e)}), 500 