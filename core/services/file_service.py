"""
FileService - Handles all file upload, validation, and processing operations.
This service extracts 200+ lines of file handling logic from app.py routes.
"""
import os
import uuid
import threading
from datetime import datetime
from typing import Tuple, List, Optional
from werkzeug.utils import secure_filename
from werkzeug.datastructures import FileStorage
from parser.tally_parser_interunit_loan_recon import parse_tally_file
from core import database


class FileService:
    """Centralizes all file operations: upload, validation, parsing, and recent uploads management."""
    
    def __init__(self):
        self.upload_folder = 'uploads'
        self.recent_uploads_file = 'recent_uploads.txt'
        self.recent_uploads_limit = 10
        self.recent_uploads_lock = threading.Lock()
        self.allowed_extensions = {'xlsx', 'xls'}
        
        # Ensure upload folder exists
        os.makedirs(self.upload_folder, exist_ok=True)
    
    def validate_file_upload(self, file: Optional[FileStorage]) -> Tuple[bool, Optional[str]]:
        """Validate uploaded file."""
        if not file:
            return False, 'No file uploaded'
        
        if file.filename == '':
            return False, 'No file selected'
        
        if not self._allowed_file(file.filename):
            return False, 'Please upload Excel files only (.xlsx, .xls)'
        
        return True, None
    
    def validate_file_pair(self, file1: FileStorage, file2: FileStorage) -> Tuple[bool, Optional[str]]:
        """Validate file pair upload."""
        if not file1 or not file2:
            return False, 'Both files are required'
        
        if file1.filename == '' or file2.filename == '':
            return False, 'Both files must be selected'
        
        if file1.filename == file2.filename:
            return False, 'Cannot upload the same file for both companies. Please select different files.'
        
        if not self._allowed_file(file1.filename) or not self._allowed_file(file2.filename):
            return False, 'Please upload Excel files only'
        
        return True, None
    
    def process_single_file(self, file: FileStorage, sheet_name: str = 'Sheet1') -> Tuple[bool, Optional[str], int]:
        """Process a single file upload."""
        # Validate file
        valid, error = self.validate_file_upload(file)
        if not valid:
            return False, error, 0
        
        try:
            # Save file temporarily
            filename = secure_filename(file.filename)
            filepath = os.path.join(self.upload_folder, filename)
            file.save(filepath)
            
            # Parse file
            df = parse_tally_file(filepath, sheet_name)
            rows_processed = len(df)
            
            # Save to database
            success, error_msg = database.save_data(df)
            
            # Clean up file
            os.remove(filepath)
            
            if success:
                # Record in recent uploads
                self.record_recent_upload(file.filename)
                return True, None, rows_processed
            else:
                return False, error_msg or 'Failed to save file', 0
                
        except Exception as e:
            # Clean up file if it exists
            if 'filepath' in locals() and os.path.exists(filepath):
                os.remove(filepath)
            return False, str(e), 0
    
    def process_file_pair(self, file1: FileStorage, sheet_name1: str,
                          file2: FileStorage, sheet_name2: str) -> Tuple[bool, Optional[str], Optional[str], int]:
        """Process a file pair upload."""
        # Validate files
        valid, error = self.validate_file_pair(file1, file2)
        if not valid:
            return False, error, None, 0
        
        try:
            # Generate unique pair ID
            pair_id = f"pair_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}"
            total_rows = 0
            
            # Process first file
            success1, error1, rows1 = self._process_single_file_with_pair_id(file1, sheet_name1, pair_id)
            if not success1:
                return False, error1, None, 0
            total_rows += rows1
            
            # Process second file
            success2, error2, rows2 = self._process_single_file_with_pair_id(file2, sheet_name2, pair_id)
            if not success2:
                return False, error2, None, 0
            total_rows += rows2
            
            # Record both files in recent uploads
            self.record_recent_upload_pair(file1.filename, file2.filename)
            
            return True, None, pair_id, total_rows
            
        except Exception as e:
            return False, str(e), None, 0
    
    def _process_single_file_with_pair_id(self, file: FileStorage, sheet_name: str, pair_id: str) -> Tuple[bool, Optional[str], int]:
        """Process a single file with pair ID."""
        try:
            # Save file temporarily
            filename = secure_filename(file.filename)
            filepath = os.path.join(self.upload_folder, filename)
            file.save(filepath)
            
            # Parse file
            df = parse_tally_file(filepath, sheet_name)
            # Add pair_id to data
            df['pair_id'] = pair_id
            rows_processed = len(df)
            
            # Save to database
            success, error_msg = database.save_data(df)
            
            # Clean up file
            os.remove(filepath)
            
            if success:
                return True, None, rows_processed
            else:
                return False, error_msg or 'Failed to save file', 0
                
        except Exception as e:
            # Clean up file if it exists
            if 'filepath' in locals() and os.path.exists(filepath):
                os.remove(filepath)
            return False, str(e), 0
    
    def record_recent_upload(self, filename: str) -> None:
        """Record a file in recent uploads list."""
        with self.recent_uploads_lock:
            try:
                if os.path.exists(self.recent_uploads_file):
                    with open(self.recent_uploads_file, 'r', encoding='utf-8') as f:
                        uploads = [line.strip() for line in f if line.strip()]
                else:
                    uploads = []
                
                # Remove if already present
                uploads = [f for f in uploads if f != filename]
                uploads.insert(0, filename)
                uploads = uploads[:self.recent_uploads_limit]
                
                with open(self.recent_uploads_file, 'w', encoding='utf-8') as f:
                    for f_name in uploads:
                        f.write(f_name + '\n')
            except Exception as e:
                print(f"Error recording recent upload: {e}")

    def record_recent_upload_pair(self, filename1: str, filename2: str) -> None:
        """Record a file pair in recent uploads list."""
        with self.recent_uploads_lock:
            try:
                if os.path.exists(self.recent_uploads_file):
                    with open(self.recent_uploads_file, 'r', encoding='utf-8') as f:
                        uploads = [line.strip() for line in f if line.strip()]
                else:
                    uploads = []
                
                # Create pair entry
                pair_entry = f"{filename1} AND {filename2}"
                
                # Remove if already present (check both individual files and pair)
                uploads = [f for f in uploads if f != filename1 and f != filename2 and f != pair_entry]
                uploads.insert(0, pair_entry)
                uploads = uploads[:self.recent_uploads_limit]
                
                with open(self.recent_uploads_file, 'w', encoding='utf-8') as f:
                    for f_name in uploads:
                        f.write(f_name + '\n')
            except Exception as e:
                print(f"Error recording recent upload pair: {e}")
    
    def get_recent_uploads(self) -> List[str]:
        """Get list of recent uploads."""
        try:
            if os.path.exists(self.recent_uploads_file):
                with open(self.recent_uploads_file, 'r', encoding='utf-8') as f:
                    uploads = [line.strip() for line in f if line.strip()]
                return uploads
            else:
                return []
        except Exception as e:
            print(f"Error getting recent uploads: {e}")
            return []
    
    def clear_recent_uploads(self) -> None:
        """Clear the recent uploads list."""
        try:
            with open(self.recent_uploads_file, 'w', encoding='utf-8') as f:
                f.write('')
        except Exception as e:
            print(f"Error clearing recent uploads: {e}")
    
    def _allowed_file(self, filename: str) -> bool:
        """Check if file extension is allowed."""
        return '.' in filename and filename.rsplit('.', 1)[1].lower() in self.allowed_extensions