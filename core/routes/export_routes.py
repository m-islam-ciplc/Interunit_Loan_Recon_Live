"""
Export Routes - Handles all download and export endpoints.
"""
from flask import Blueprint, request, jsonify
from core.services.export_service import ExportService

export_bp = Blueprint('export', __name__)

@export_bp.route('/download-matches', methods=['GET'])
def download_matches():
    """Download auto-matched transactions as Excel - Only high-confidence auto-matches are included"""
    try:
        filters = {
            'lender_company': request.args.get('lender_company'),
            'borrower_company': request.args.get('borrower_company'),
            'month': request.args.get('month'),
            'year': request.args.get('year')
        }
        
        export_service = ExportService()
        return export_service.export_matched_transactions(filters)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@export_bp.route('/download-unmatched', methods=['GET'])
def download_unmatched():
    """Download unmatched transactions as Excel - REFACTORED to use ExportService"""
    try:
        filters = {
            'lender_company': request.args.get('lender_company'),
            'borrower_company': request.args.get('borrower_company'),
            'month': request.args.get('month'),
            'year': request.args.get('year')
        }
        
        export_service = ExportService()
        return export_service.export_unmatched_transactions(filters)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@export_bp.route('/export', methods=['GET'])
def export_data():
    """Export filtered data to Excel - REFACTORED to use ExportService"""
    from core.services.export_service import ExportService
    
    try:
        filters = {
            'lender': request.args.get('lender'),
            'borrower': request.args.get('borrower'),
            'statement_month': request.args.get('statement_month'),
            'statement_year': request.args.get('statement_year'),
            'vch_type': request.args.get('vch_type'),
            'entered_by': request.args.get('entered_by')
        }
        
        export_service = ExportService()
        return export_service.export_filtered_data(filters)
    except Exception as e:
        return jsonify({'error': str(e)}), 500 