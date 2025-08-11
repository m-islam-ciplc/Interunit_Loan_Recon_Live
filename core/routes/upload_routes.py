"""
Upload Routes - Handles all file upload and management endpoints.
"""
from flask import Blueprint, request, jsonify
from core.services.file_service import FileService

upload_bp = Blueprint('upload', __name__)

@upload_bp.route('/recent-uploads', methods=['GET'])
def get_recent_uploads():
    """Get recent uploads - REFACTORED to use FileService"""
    try:
        file_service = FileService()
        uploads = file_service.get_recent_uploads()
        return jsonify({'recent_uploads': uploads})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@upload_bp.route('/clear-recent-uploads', methods=['POST'])
def clear_recent_uploads():
    """Clear recent uploads - REFACTORED to use FileService"""
    try:
        file_service = FileService()
        file_service.clear_recent_uploads()
        return jsonify({'message': 'Recent uploads cleared.'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@upload_bp.route('/upload', methods=['POST'])
def upload_file():
    """Upload and process file - REFACTORED to use FileService"""
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file uploaded'}), 400
        
        file = request.files['file']
        sheet_name = request.form.get('sheet_name', 'Sheet1')
        
        # Use FileService for all file operations
        file_service = FileService()
        success, error, rows_processed = file_service.process_single_file(file, sheet_name)
        
        if success:
            return jsonify({
                'message': 'File processed successfully',
                'rows_processed': rows_processed
            })
        else:
            return jsonify({'error': error}), 400
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@upload_bp.route('/upload-pair', methods=['POST'])
def upload_file_pair():
    """Upload and process file pair - REFACTORED to use FileService"""
    try:
        if 'file1' not in request.files or 'file2' not in request.files:
            return jsonify({'error': 'Both files are required'}), 400
        
        file1 = request.files['file1']
        file2 = request.files['file2']
        sheet_name1 = request.form.get('sheet_name1', 'Sheet1')
        sheet_name2 = request.form.get('sheet_name2', 'Sheet1')
        
        # Use FileService for all file pair operations
        file_service = FileService()
        success, error, pair_id, total_rows = file_service.process_file_pair(
            file1, sheet_name1, file2, sheet_name2
        )
        
        if success:
            return jsonify({
                'message': 'File pair processed successfully',
                'rows_processed': total_rows,
                'pair_id': pair_id
            })
        else:
            return jsonify({'error': error}), 400
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500 