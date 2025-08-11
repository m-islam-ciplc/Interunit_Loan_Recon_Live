# Interunit Loan Reconciliation System

A professional Flask-based web application for automating interunit loan reconciliation between companies. This system processes Tally ledger files, matches transactions, and provides comprehensive reconciliation reports.

## 🚀 Features

- **File Upload & Processing**: Handle Excel (.xlsx, .xls) files from Tally accounting software
- **Automated Matching**: Intelligent transaction matching using multiple criteria (PO, LC, LOAN_ID, etc.)
- **Manual Reconciliation**: User-friendly interface for manual transaction matching
- **Data Export**: Generate formatted Excel reports for matched and unmatched transactions
- **Company Pair Management**: Support for multiple company relationships
- **Database Management**: MySQL backend with comprehensive data handling
- **Production Ready**: WSGI server support with gunicorn

## 🏗️ Architecture

```
├── app_interunit_loan_recon.py    # Main Flask application
├── core/                          # Core business logic
│   ├── database.py               # Database operations
│   ├── matching.py               # Transaction matching algorithms
│   ├── config.py                 # Configuration settings
│   ├── bank_config.py            # Bank-specific configurations
│   ├── routes/                   # API and UI route handlers
│   └── services/                 # Business logic services
├── parser/                        # File parsing modules
│   └── tally_parser_interunit_loan_recon.py
├── templates/                     # HTML templates
├── static/                        # CSS, JS, and static assets
└── uploads/                       # File upload directory
```

## 🛠️ Technology Stack

- **Backend**: Flask (Python web framework)
- **Database**: MySQL with SQLAlchemy ORM
- **File Processing**: pandas, openpyxl
- **Production Server**: Gunicorn WSGI server
- **Frontend**: Bootstrap 5, vanilla JavaScript
- **File Handling**: Werkzeug utilities

## 📋 Prerequisites

- Python 3.8+
- MySQL 5.7+ or 8.0+
- Virtual environment (recommended)

## 🚀 Installation & Setup

### 1. Clone the Repository
```bash
git clone <repository-url>
cd Interunit_Loan_Recon_Live
```

### 2. Create Virtual Environment
```bash
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Database Setup
```sql
-- Create database and user
CREATE DATABASE interunit_loan_recon_db;
CREATE USER 'interunit_loan_recon_user'@'localhost' IDENTIFIED BY 'abc123';
GRANT ALL PRIVILEGES ON interunit_loan_recon_db.* TO 'interunit_loan_recon_user'@'localhost';
FLUSH PRIVILEGES;

-- Run the SQL script
mysql -u root -p interunit_loan_recon_db < db_query_interunit_loan_recon.sql
```

### 5. Configuration
Update `core/config.py` with your database credentials:
```python
MYSQL_USER = 'your_username'
MYSQL_PASSWORD = 'your_password'
MYSQL_HOST = 'your_host'
MYSQL_DB = 'your_database'
```

## 🏃‍♂️ Running the Application

### Development Mode
```bash
source .venv/bin/activate
python app_interunit_loan_recon.py
```

### Production Mode (Recommended for servers)
```bash
source .venv/bin/activate
gunicorn app_interunit_loan_recon:app --bind 0.0.0.0:5001 --workers 4 --daemon
```

## 📖 Usage Guide

### 1. Upload Ledger Files
- Navigate to the upload section
- Select Excel files from Tally software
- Choose appropriate sheet names
- Upload files for both companies in a pair

### 2. Run Reconciliation
- Access the reconciliation module
- Review auto-matched transactions
- Manually match remaining transactions
- Confirm matches for audit trail

### 3. View Results
- Check matched transactions
- Review unmatched items
- Export reports as needed

### 4. Database Management
- Monitor data integrity
- Clear old records
- Reset matching status if needed

## 🔧 API Endpoints

### Upload Routes
- `POST /api/upload` - Single file upload
- `POST /api/upload-pair` - File pair upload
- `GET /api/recent-uploads` - Get recent uploads
- `POST /api/clear-recent-uploads` - Clear upload history

### Data Routes
- `GET /api/data` - Retrieve transaction data
- `GET /api/filters` - Get available filters
- `GET /api/column-order` - Get database column order

### Reconciliation Routes
- `POST /api/run-matching` - Execute matching algorithm
- `POST /api/update-matches` - Update match status
- `GET /api/matched-data` - Get matched transactions
- `GET /api/unmatched-data` - Get unmatched transactions

### Export Routes
- `GET /api/export-matched` - Export matched transactions
- `GET /api/export-unmatched` - Export unmatched transactions
- `GET /api/export-filtered` - Export filtered data

## 🗄️ Database Schema

### Main Tables
- `tally_data` - Raw transaction data from Tally files
- `company_pairs` - Company relationship mappings
- `match_status` - Transaction matching status

### Key Fields
- `uid` - Unique transaction identifier
- `lender` - Lending company
- `borrower` - Borrowing company
- `amount` - Transaction amount
- `date` - Transaction date
- `match_status` - Current matching status

## 🔒 Security Considerations

- File upload validation (Excel files only)
- Secure filename handling
- Database connection security
- Input sanitization
- Access control (implement as needed)

## 📊 Performance Features

- Chunked database insertions
- Efficient transaction matching algorithms
- Background file processing
- Optimized database queries
- Worker process management

## 🚨 Troubleshooting

### Common Issues
1. **Database Connection Error**: Check MySQL credentials and service status
2. **File Upload Failures**: Verify file format and permissions
3. **Memory Issues**: Reduce worker count in gunicorn
4. **Port Conflicts**: Change port in gunicorn bind parameter

### Logs
- Check application logs for errors
- Monitor gunicorn process status
- Verify database connectivity

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## 📄 License

[Add your license information here]

## 👥 Support

For technical support or questions:
- Create an issue in the repository
- Contact the development team
- Check documentation and troubleshooting guides

## 🔄 Version History

- **v1.0.0** - Initial release with core reconciliation features
- **v1.1.0** - Added export functionality and improved matching
- **v1.2.0** - Production deployment support with gunicorn

---

**Built with ❤️ for professional financial reconciliation needs**
