// Interunit Loan Reconciliation - JavaScript

// Initialize when page loads
document.addEventListener('DOMContentLoaded', function() {
    loadData();
    if (document.getElementById('recent-uploads-list')) {
        loadRecentUploads();
    }
});

// Handle browser back/forward buttons
window.addEventListener('popstate', function(event) {
    if (event.state && event.state.tab) {
        showTab(event.state.tab);
    }
});

// Prevent submenu collapse when submenu items are clicked
document.addEventListener('DOMContentLoaded', function() {
    const submenuItems = document.querySelectorAll('.submenu-item');
    submenuItems.forEach(item => {
        item.addEventListener('click', function(e) {
            // Prevent the click from bubbling up to the parent collapse trigger
            e.stopPropagation();
            e.preventDefault();
            
            // Get the href and navigate programmatically
            const href = this.getAttribute('href');
            if (href) {
                // Use showTab instead of direct navigation to maintain URL structure
                const tabName = href.substring(1); // Remove the leading slash
                showTab(tabName);
            }
        });
    });
});

// Tab switching function
function showTab(tabName) {
    // Hide all tab panes
    const tabPanes = document.querySelectorAll('.tab-pane');
    tabPanes.forEach(pane => {
        pane.style.display = 'none';
    });
    
    // Show selected tab pane
    const selectedPane = document.getElementById('pane-' + tabName);
    if (selectedPane) {
        selectedPane.style.display = 'block';
        
        // Update URL without page reload
        const url = '/' + tabName;
        window.history.pushState({ tab: tabName }, '', url);
        
        // If switching to data-table tab, load data
        if (tabName === 'data-table') {
            loadData();
        }
        
        // If switching to reconciliation tab, load company pairs
        if (tabName === 'reconciliation') {
            loadReconciliationCompanyPairs();
        }
        
        // If switching to matched-results tab, load company pairs
        if (tabName === 'matched-results') {
            loadMatchedCompanyPairs();
        }
        
        // If switching to unmatched-results tab, load company pairs
        if (tabName === 'unmatched-results') {
            loadUnmatchedCompanyPairs();
        }
    }
}

// Handle file selection with SheetJS
function handleFileSelect(input, fileNumber) {
    const file = input.files[0];
    const fileChosenSpan = document.getElementById(`file-chosen-${fileNumber}`);
    const sheetRow = document.getElementById(`sheet-row-${fileNumber}`);
    const sheetSelect = sheetRow.querySelector('.sheet-select');
    const parseBtn = document.getElementById('parse-btn');
    
    if (file) {
        // Update file name display
        fileChosenSpan.textContent = file.name;
        
        // Read Excel file with SheetJS
        const reader = new FileReader();
        reader.onload = function(e) {
            try {
                const data = new Uint8Array(e.target.result);
                const workbook = XLSX.read(data, { type: 'array' });
                
                // Clear existing options
                sheetSelect.innerHTML = '';
                
                // Add sheet names to dropdown
                workbook.SheetNames.forEach(sheetName => {
                    const option = document.createElement('option');
                    option.value = sheetName;
                    option.textContent = sheetName;
                    sheetSelect.appendChild(option);
                });
                
                // Show sheet selection row
                sheetRow.style.display = 'flex';
                
                // Enable parse button if both files are selected
                checkBothFilesSelected();
                
            } catch (error) {
                console.error('Error reading Excel file:', error);
                fileChosenSpan.textContent = 'Error reading file';
                parseBtn.disabled = true;
            }
        };
        reader.readAsArrayBuffer(file);
    } else {
        fileChosenSpan.textContent = 'No file chosen';
        sheetRow.style.display = 'none';
        parseBtn.disabled = true;
    }
}

function checkBothFilesSelected() {
    const file1 = document.querySelector('input[name="file1"]').files[0];
    const file2 = document.querySelector('input[name="file2"]').files[0];
    const sheet1 = document.getElementById('sheet-select-1').value;
    const sheet2 = document.getElementById('sheet-select-2').value;
    
    const parseBtn = document.getElementById('parse-btn');
    const uploadMsg = document.getElementById('upload-msg');
    
    // Check if both files are selected
    if (file1 && file2) {
        // Check if same file is selected
        if (file1.name === file2.name) {
            uploadMsg.innerHTML = '<div class="alert alert-warning"><i class="bi bi-exclamation-triangle me-2"></i>Warning: Same file selected for both companies. Please select different files.</div>';
            parseBtn.disabled = true;
            return;
        } else {
            uploadMsg.innerHTML = '';
        }
    }
    
    parseBtn.disabled = !(file1 && file2 && sheet1 && sheet2);
}

// Handle form submission
document.getElementById('tally-upload-form').addEventListener('submit', function(e) {
    e.preventDefault();
    uploadFile();
});

// Upload file function
async function uploadFile() {
    const formData = new FormData();
    const fileInput1 = document.querySelector('input[name="file1"]');
    const fileInput2 = document.querySelector('input[name="file2"]');
    const sheetSelect1 = document.getElementById('sheet-select-1');
    const sheetSelect2 = document.getElementById('sheet-select-2');
    const parseBtn = document.getElementById('parse-btn');
    const uploadMsg = document.getElementById('upload-msg');
    const uploadResult = document.getElementById('upload-result');
    
    if (!fileInput1.files[0] || !fileInput2.files[0]) {
        uploadMsg.innerHTML = '<div class="alert alert-danger"><i class="bi bi-exclamation-circle me-2"></i>Please select both files to upload.</div>';
        return;
    }
    
    if (!sheetSelect1.value || !sheetSelect2.value) {
        uploadMsg.innerHTML = '<div class="alert alert-danger"><i class="bi bi-exclamation-circle me-2"></i>Please select sheets for both files.</div>';
        return;
    }
    
    formData.append('file1', fileInput1.files[0]);
    formData.append('file2', fileInput2.files[0]);
    formData.append('sheet_name1', sheetSelect1.value);
    formData.append('sheet_name2', sheetSelect2.value);
    
    // Show loading
    parseBtn.disabled = true;
    parseBtn.textContent = 'Processing...';
    uploadMsg.textContent = '';
    uploadResult.innerHTML = '<div class="alert alert-info"><i class="bi bi-info-circle me-2"></i>Uploading file pair...</div>';
    
    try {
        const response = await fetch('/api/upload-pair', {
            method: 'POST',
            body: formData
        });
        
        const result = await response.json();
        
        if (response.ok) {
            uploadResult.innerHTML = `<div class="alert alert-success"><i class="bi bi-check-circle me-2"></i>File pair uploaded successfully! ${result.rows_processed} rows processed. Pair ID: <code>${result.pair_id}</code></div>`;
            
            // Reset form
            fileInput1.value = '';
            fileInput2.value = '';
            document.getElementById('file-chosen-1').textContent = 'No file chosen';
            document.getElementById('file-chosen-2').textContent = 'No file chosen';
            document.getElementById('sheet-row-1').style.display = 'none';
            document.getElementById('sheet-row-2').style.display = 'none';
            parseBtn.disabled = true;
            
            // Reload data
            loadData();
            loadRecentUploads();
            
            // Clear success message after 8 seconds (longer to show pair ID)
            setTimeout(() => {
                uploadResult.innerHTML = '';
            }, 8000);
            
        } else {
            uploadResult.innerHTML = `<div class="alert alert-danger"><i class="bi bi-exclamation-circle me-2"></i>Upload failed: ${result.error}</div>`;
        }
        
    } catch (error) {
        uploadResult.innerHTML = `<div class="alert alert-danger"><i class="bi bi-exclamation-circle me-2"></i>Upload failed: ${error.message}</div>`;
    } finally {
        parseBtn.disabled = false;
        parseBtn.textContent = 'Upload Pair';
    }
}

// Load data from API
async function loadData() {
    try {
        const response = await fetch('/api/data');
        const result = await response.json();
        
        if (response.ok) {
            displayData(result.data, result.column_order);
        } else {
            console.error('Error loading data:', result.error);
        }
    } catch (error) {
        console.error('Error loading data:', error);
    }
}

// Display data in table
function displayData(data, columnOrder) {
    const resultDiv = document.getElementById('data-table-result');
    
    if (!data || data.length === 0) {
        resultDiv.innerHTML = `
            <div class="alert alert-info text-center">
                <i class="bi bi-info-circle me-2"></i>No data available. Upload a file to get started.
            </div>
        `;
        return;
    }
    
    // Use the column order from backend, fallback to Object.keys if not provided
    const columns = columnOrder || Object.keys(data[0]);
    
    // Debug: Print the column order received by frontend
    console.log("Frontend received columns:", columns);
    
    let tableHTML = `
        <div class="report-table-wrapper" style="max-height: 70vh; overflow-y: auto;">
            <table class="table matched-transactions-table">
                <thead>
                    <tr>
                        ${columns.map(col => {
                            // Map column names to data-column attributes and CSS classes
                            const columnMapping = {
                                'UID': { attr: 'uid', class: 'uid-cell' },
                                'uid': { attr: 'uid', class: 'uid-cell' },
                                'Lender': { attr: 'lender', class: 'lender-cell' },
                                'lender': { attr: 'lender', class: 'lender-cell' },
                                'Borrower': { attr: 'borrower', class: 'borrower-cell' },
                                'borrower': { attr: 'borrower', class: 'borrower-cell' },
                                'Date': { attr: 'date', class: 'date-cell' },
                                'date': { attr: 'date', class: 'date-cell' },
                                'Particulars': { attr: 'particulars', class: 'particulars-cell' },
                                'particulars': { attr: 'particulars', class: 'particulars-cell' },
                                'Vch_Type': { attr: 'vch_type', class: 'vch-type-cell' },
                                'vch_type': { attr: 'vch_type', class: 'vch-type-cell' },
                                'Vch_No': { attr: 'vch_no', class: 'vch-no-cell' },
                                'vch_no': { attr: 'vch_no', class: 'vch-no-cell' },
                                'Debit': { attr: 'debit', class: 'amount-cell' },
                                'debit': { attr: 'debit', class: 'amount-cell' },
                                'Credit': { attr: 'credit', class: 'amount-cell' },
                                'credit': { attr: 'credit', class: 'amount-cell' },
                                'entered_by': { attr: 'entered_by', class: 'entered-by-cell' },
                                'input_date': { attr: 'input_date', class: 'input-date-cell' },
                                'role': { attr: 'role', class: 'role-cell' },
                                'statement_month': { attr: 'statement_month', class: 'statement-month-cell' },
                                'statement_year': { attr: 'statement_year', class: 'statement-year-cell' }
                            };
                            
                            const mapping = columnMapping[col] || { attr: col.toLowerCase(), class: '' };
                            return `<th data-column="${mapping.attr}" class="${mapping.class} text-center">${col}</th>`;
                        }).join('')}
                    </tr>
                </thead>
                <tbody>
    `;
    
    data.forEach(row => {
        tableHTML += `
            <tr>
                ${columns.map(col => {
                    let value = row[col];
                    if (value === null || value === undefined) {
                        value = '';
                    } else {
                        // Format date columns to YYYY-MM-DD
                        if (col.toLowerCase().includes('date') || col === 'Date') {
                            value = formatDate(value);
                        }
                    }
                    
                    // Map column names to data-column attributes and CSS classes
                    const columnMapping = {
                        'UID': { attr: 'uid', class: 'uid-cell' },
                        'uid': { attr: 'uid', class: 'uid-cell' },
                        'Lender': { attr: 'lender', class: 'lender-cell' },
                        'lender': { attr: 'lender', class: 'lender-cell' },
                        'Borrower': { attr: 'borrower', class: 'borrower-cell' },
                        'borrower': { attr: 'borrower', class: 'borrower-cell' },
                        'Date': { attr: 'date', class: 'date-cell' },
                        'date': { attr: 'date', class: 'date-cell' },
                        'Particulars': { attr: 'particulars', class: 'particulars-cell' },
                        'particulars': { attr: 'particulars', class: 'particulars-cell' },
                        'Vch_Type': { attr: 'vch_type', class: 'vch-type-cell' },
                        'vch_type': { attr: 'vch_type', class: 'vch-type-cell' },
                        'Vch_No': { attr: 'vch_no', class: 'vch-no-cell' },
                        'vch_no': { attr: 'vch_no', class: 'vch-no-cell' },
                        'Debit': { attr: 'debit', class: 'amount-cell text-end' },
                        'debit': { attr: 'debit', class: 'amount-cell text-end' },
                        'Credit': { attr: 'credit', class: 'amount-cell text-end' },
                        'credit': { attr: 'credit', class: 'amount-cell text-end' },
                        'entered_by': { attr: 'entered_by', class: 'entered-by-cell' },
                        'input_date': { attr: 'input_date', class: 'input-date-cell' },
                        'role': { attr: 'role', class: 'role-cell' },
                        'statement_month': { attr: 'statement_month', class: 'statement-month-cell' },
                        'statement_year': { attr: 'statement_year', class: 'statement-year-cell' }
                    };
                    
                    const mapping = columnMapping[col] || { attr: col.toLowerCase(), class: '' };
                    return `<td data-column="${mapping.attr}" class="${mapping.class}">${value}</td>`;
                }).join('')}
            </tr>
        `;
    });
    
    tableHTML += `
            </div>
        </div>
        <div class="alert alert-light mt-2">
            <i class="bi bi-info-circle me-2"></i>Total records: ${data.length}
        </div>
    `;
    
    resultDiv.innerHTML = tableHTML;
}

// Helper function to show Bootstrap notifications
function showNotification(message, type = 'info', targetId = 'reconciliation-result') {
    const targetDiv = document.getElementById(targetId);
    if (targetDiv) {
        const alertClass = type === 'error' ? 'alert-danger' : 
                          type === 'success' ? 'alert-success' : 
                          type === 'warning' ? 'alert-warning' : 'alert-info';
        const iconClass = type === 'error' ? 'bi-exclamation-circle' : 
                         type === 'success' ? 'bi-check-circle' : 
                         type === 'warning' ? 'bi-exclamation-triangle' : 'bi-info-circle';
        
        targetDiv.innerHTML = `<div class="alert ${alertClass}"><i class="bi ${iconClass} me-2"></i>${message}</div>`;
        
        // Auto-remove after 5 seconds for success/info messages
        if (type === 'success' || type === 'info') {
            setTimeout(() => {
                if (targetDiv.innerHTML.includes(message)) {
                    targetDiv.innerHTML = '';
                }
            }, 5000);
        }
    }
}

// Helper function to get badge class for match status
function getStatusBadgeClass(status) {
    switch(status) {
        case 'confirmed':
            return 'bg-success';
        case 'matched':
            return 'bg-warning';
        case 'unmatched':
        default:
            return 'bg-secondary';
    }
}

// Helper function to format match method names
function formatMatchMethod(method) {
    if (!method) return '';
    
    switch(method) {
        case 'reference_match':
            return 'Reference Match';
        case 'similarity_match':
            return 'Similarity Match';
        case 'cross_reference':
            return 'Cross Reference';
        case 'fallback_match':
            return 'Fallback Match';
        default:
            return method;
    }
}

// Update reconciliation function to use company pairs
async function runReconciliation() {
    const resultDiv = document.getElementById('reconciliation-result');
    
    // Get selected company pair and period
    const companySelect = document.getElementById('reconciliation-company-pair-select');
    const periodSelect = document.getElementById('reconciliation-period-select');
    const companyPair = companySelect ? companySelect.value : '';
    const period = periodSelect ? periodSelect.value : '';
    
    let lenderCompany = '';
    let borrowerCompany = '';
    let month = '';
    let year = '';
    
    if (companyPair && companyPair.includes('↔')) {
        const parts = companyPair.split('↔').map(s => s.trim());
        lenderCompany = parts[0];
        borrowerCompany = parts[1];
    }
    
    if (period && period !== '-- Select Statement Period --') {
        const periodParts = period.split(' ');
        if (periodParts.length === 2) {
            month = periodParts[0];
            year = periodParts[1];
        }
    }
    
    // Show detailed notification about what's being reconciled
    let notificationMessage = '<div class="alert alert-info" role="alert">';
    notificationMessage += '<i class="bi bi-info-circle me-2"></i>';
    notificationMessage += '<strong>Running Reconciliation for:</strong><br>';
    
    if (lenderCompany && borrowerCompany) {
        notificationMessage += `<strong>Company Pair:</strong> ${lenderCompany} ↔ ${borrowerCompany}<br>`;
    } else {
        notificationMessage += '<strong>Company Pair:</strong> All Companies<br>';
    }
    
    if (month && year) {
        notificationMessage += `<strong>Statement Period:</strong> ${month} ${year}<br>`;
    } else {
        notificationMessage += '<strong>Statement Period:</strong> All Periods<br>';
    }
    
    notificationMessage += '<small class="text-muted">Processing transactions...</small>';
    notificationMessage += '</div>';
    
    resultDiv.innerHTML = notificationMessage;
    
    try {
        const response = await fetch('/api/reconcile', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                lender_company: lenderCompany,
                borrower_company: borrowerCompany,
                month: month,
                year: year
            })
        });
        
        const result = await response.json();
        
        if (response.ok) {
            // Create new reconciliation result entry
            const timestamp = new Date().toLocaleString();
            const reconciliationResult = {
                timestamp: timestamp,
                companyPair: lenderCompany && borrowerCompany ? `${lenderCompany} ↔ ${borrowerCompany}` : 'All Companies',
                statementPeriod: month && year ? `${month} ${year}` : 'All Periods',
                matchesFound: result.matches_found
            };
            
            // Add to reconciliation history
            addReconciliationToHistory(reconciliationResult);
            
            // Display all reconciliation history
            displayReconciliationHistory();
            
        } else {
            // Create error notification
            let errorMessage = '<div class="alert alert-danger" role="alert">';
            errorMessage += '<i class="bi bi-exclamation-triangle me-2"></i>';
            errorMessage += '<strong>Reconciliation Failed!</strong><br>';
            errorMessage += `<strong>Company Pair:</strong> ${lenderCompany && borrowerCompany ? `${lenderCompany} ↔ ${borrowerCompany}` : 'All Companies'}<br>`;
            errorMessage += `<strong>Statement Period:</strong> ${month && year ? `${month} ${year}` : 'All Periods'}<br>`;
            errorMessage += `<strong>Error:</strong> ${result.error}`;
            errorMessage += '</div>';
            
            resultDiv.innerHTML = errorMessage;
        }
        
    } catch (error) {
        // Create error notification for network/technical errors
        let errorMessage = '<div class="alert alert-danger" role="alert">';
        errorMessage += '<i class="bi bi-exclamation-triangle me-2"></i>';
        errorMessage += '<strong>Reconciliation Failed!</strong><br>';
        errorMessage += `<strong>Company Pair:</strong> ${lenderCompany && borrowerCompany ? `${lenderCompany} ↔ ${borrowerCompany}` : 'All Companies'}<br>`;
        errorMessage += `<strong>Statement Period:</strong> ${month && year ? `${month} ${year}` : 'All Periods'}<br>`;
        errorMessage += `<strong>Error:</strong> ${error.message}`;
        errorMessage += '</div>';
        
        resultDiv.innerHTML = errorMessage;
    }
}

async function loadMatches() {
    const resultDiv = document.getElementById('reconciliation-result');
    
    // Check if there's reconciliation history
    if (reconciliationHistory.length > 0) {
        // If there's reconciliation history, don't override it
        return;
    }
    
    // Get selected company pair and period
    const companySelect = document.getElementById('matched-company-pair-select');
    const periodSelect = document.getElementById('matched-period-select');
    const companyPair = companySelect ? companySelect.value : '';
    const period = periodSelect ? periodSelect.value : '';
    let lenderCompany = '';
    let borrowerCompany = '';
    let month = '';
    let year = '';
    if (companyPair && companyPair.includes('↔')) {
        // Format: "Company1 ↔ Company2"
        const parts = companyPair.split('↔').map(s => s.trim());
        lenderCompany = parts[0];
        borrowerCompany = parts[1];
    }
    if (period && period !== '-- All Periods --') {
        // Format: "Month Year"
        const periodParts = period.split(' ');
        if (periodParts.length === 2) {
            month = periodParts[0];
            year = periodParts[1];
        }
    }
    
    // Show loading notification with filter details
    let loadingMessage = '<div class="alert alert-info" role="alert">';
    loadingMessage += '<i class="bi bi-info-circle me-2"></i>';
    loadingMessage += '<strong>Loading Matched Results for:</strong><br>';
    
    if (lenderCompany && borrowerCompany) {
        loadingMessage += `<strong>Company Pair:</strong> ${lenderCompany} ↔ ${borrowerCompany}<br>`;
    } else {
        loadingMessage += '<strong>Company Pair:</strong> All Companies<br>';
    }
    
    if (month && year) {
        loadingMessage += `<strong>Statement Period:</strong> ${month} ${year}<br>`;
    } else {
        loadingMessage += '<strong>Statement Period:</strong> All Periods<br>';
    }
    
    loadingMessage += '<small class="text-muted">Fetching matched transactions...</small>';
    loadingMessage += '</div>';
    
    resultDiv.innerHTML = loadingMessage;
    
    // Build query string
    let url = '/api/matches';
    const params = [];
    if (lenderCompany && borrowerCompany) {
        params.push(`lender_company=${encodeURIComponent(lenderCompany)}`);
        params.push(`borrower_company=${encodeURIComponent(borrowerCompany)}`);
    }
    if (month) params.push(`month=${encodeURIComponent(month)}`);
    if (year) params.push(`year=${encodeURIComponent(year)}`);
    if (params.length > 0) {
        url += '?' + params.join('&');
    }
    try {
        const response = await fetch(url);
        const result = await response.json();
        if (response.ok) {
            displayMatches(result.matches);
        } else {
            // Create error notification
            let errorMessage = '<div class="alert alert-danger" role="alert">';
            errorMessage += '<i class="bi bi-exclamation-triangle me-2"></i>';
            errorMessage += '<strong>Failed to Load Matched Results!</strong><br>';
            errorMessage += `<strong>Company Pair:</strong> ${lenderCompany && borrowerCompany ? `${lenderCompany} ↔ ${borrowerCompany}` : 'All Companies'}<br>`;
            errorMessage += `<strong>Statement Period:</strong> ${month && year ? `${month} ${year}` : 'All Periods'}<br>`;
            errorMessage += `<strong>Error:</strong> ${result.error}`;
            errorMessage += '</div>';
            
            resultDiv.innerHTML = errorMessage;
        }
    } catch (error) {
        // Create error notification for network/technical errors
        let errorMessage = '<div class="alert alert-danger" role="alert">';
        errorMessage += '<i class="bi bi-exclamation-triangle me-2"></i>';
        errorMessage += '<strong>Failed to Load Matched Results!</strong><br>';
        errorMessage += `<strong>Company Pair:</strong> ${lenderCompany && borrowerCompany ? `${lenderCompany} ↔ ${borrowerCompany}` : 'All Companies'}<br>`;
        errorMessage += `<strong>Statement Period:</strong> ${month && year ? `${month} ${year}` : 'All Periods'}<br>`;
        errorMessage += `<strong>Error:</strong> ${error.message}`;
        errorMessage += '</div>';
        
        resultDiv.innerHTML = errorMessage;
    }
}

async function loadMatchesInViewer() {
    const resultDiv = document.getElementById('matched-results-display');
    
    // Get selected company pair and period
    const companySelect = document.getElementById('matched-company-pair-select');
    const periodSelect = document.getElementById('matched-period-select');
    const companyPair = companySelect ? companySelect.value : '';
    const period = periodSelect ? periodSelect.value : '';
    
    let lenderCompany = '';
    let borrowerCompany = '';
    let month = '';
    let year = '';
    
    if (companyPair && companyPair.includes('↔')) {
        const parts = companyPair.split('↔').map(s => s.trim());
        lenderCompany = parts[0];
        borrowerCompany = parts[1];
    }
    
    if (period && period !== '-- All Periods --') {
        const periodParts = period.split(' ');
        if (periodParts.length === 2) {
            month = periodParts[0];
            year = periodParts[1];
        }
    }
    
    // Show loading notification with filter details
    let loadingMessage = '<div class="alert alert-info" role="alert">';
    loadingMessage += '<i class="bi bi-info-circle me-2"></i>';
    loadingMessage += '<strong>Loading Matched Results for:</strong><br>';
    
    if (lenderCompany && borrowerCompany) {
        loadingMessage += `<strong>Company Pair:</strong> ${lenderCompany} ↔ ${borrowerCompany}<br>`;
    } else {
        loadingMessage += '<strong>Company Pair:</strong> All Companies<br>';
    }
    
    if (month && year) {
        loadingMessage += `<strong>Statement Period:</strong> ${month} ${year}<br>`;
    } else {
        loadingMessage += '<strong>Statement Period:</strong> All Periods<br>';
    }
    
    loadingMessage += '<small class="text-muted">Fetching matched transactions...</small>';
    loadingMessage += '</div>';
    
    resultDiv.innerHTML = loadingMessage;
    
    // Build query string
    let url = '/api/matches';
    const params = [];
    if (lenderCompany && borrowerCompany) {
        params.push(`lender_company=${encodeURIComponent(lenderCompany)}`);
        params.push(`borrower_company=${encodeURIComponent(borrowerCompany)}`);
    }
    if (month) params.push(`month=${encodeURIComponent(month)}`);
    if (year) params.push(`year=${encodeURIComponent(year)}`);
    if (params.length > 0) {
        url += '?' + params.join('&');
    }
    
    try {
        const response = await fetch(url);
        const result = await response.json();
        
        if (response.ok) {
            // Pass filter context to displayMatches for context header
            const filterContext = {
                lenderCompany: lenderCompany,
                borrowerCompany: borrowerCompany,
                month: month,
                year: year
            };
            displayMatches(result.matches, 'matched-results-display', filterContext);
        } else {
            // Create error notification
            let errorMessage = '<div class="alert alert-danger" role="alert">';
            errorMessage += '<i class="bi bi-exclamation-triangle me-2"></i>';
            errorMessage += '<strong>Failed to Load Matched Results!</strong><br>';
            errorMessage += `<strong>Company Pair:</strong> ${lenderCompany && borrowerCompany ? `${lenderCompany} ↔ ${borrowerCompany}` : 'All Companies'}<br>`;
            errorMessage += `<strong>Statement Period:</strong> ${month && year ? `${month} ${year}` : 'All Periods'}<br>`;
            errorMessage += `<strong>Error:</strong> ${result.error}`;
            errorMessage += '</div>';
            
            resultDiv.innerHTML = errorMessage;
        }
        
    } catch (error) {
        // Create error notification for network/technical errors
        let errorMessage = '<div class="alert alert-danger" role="alert">';
        errorMessage += '<i class="bi bi-exclamation-triangle me-2"></i>';
        errorMessage += '<strong>Failed to Load Matched Results!</strong><br>';
        errorMessage += `<strong>Company Pair:</strong> ${lenderCompany && borrowerCompany ? `${lenderCompany} ↔ ${borrowerCompany}` : 'All Companies'}<br>`;
        errorMessage += `<strong>Statement Period:</strong> ${month && year ? `${month} ${year}` : 'All Periods'}<br>`;
        errorMessage += `<strong>Error:</strong> ${error.message}`;
        errorMessage += '</div>';
        
        resultDiv.innerHTML = errorMessage;
    }
}



function formatAuditInfo(auditInfoStr) {
    if (!auditInfoStr) return '';
    try {
        const auditInfo = JSON.parse(auditInfoStr);
        let formattedInfo = '';
        
        // Format match type and details based on type
        switch(auditInfo.match_type) {
            case 'PO':
                formattedInfo += `PO Match\n`;
                if (auditInfo.po_number) {
                    formattedInfo += `PO Number: ${auditInfo.po_number}\n`;
                }
                if (auditInfo.lender_amount) {
                    formattedInfo += `Lender Amount: ${auditInfo.lender_amount}\n`;
                }
                if (auditInfo.borrower_amount) {
                    formattedInfo += `Borrower Amount: ${auditInfo.borrower_amount}\n`;
                }
                break;
            case 'LC':
                formattedInfo += `LC Match\n`;
                if (auditInfo.lc_number) {
                    formattedInfo += `LC Number: ${auditInfo.lc_number}\n`;
                }
                if (auditInfo.lender_amount) {
                    formattedInfo += `Lender Amount: ${auditInfo.lender_amount}\n`;
                }
                if (auditInfo.borrower_amount) {
                    formattedInfo += `Borrower Amount: ${auditInfo.borrower_amount}\n`;
                }
                break;
            case 'LOAN_ID':
                formattedInfo += `Loan ID Match\n`;
                if (auditInfo.loan_id) {
                    formattedInfo += `Loan ID: ${auditInfo.loan_id}\n`;
                }
                if (auditInfo.lender_amount) {
                    formattedInfo += `Lender Amount: ${auditInfo.lender_amount}\n`;
                }
                if (auditInfo.borrower_amount) {
                    formattedInfo += `Borrower Amount: ${auditInfo.borrower_amount}\n`;
                }
                break;
            case 'SALARY':
                formattedInfo += `Salary Match\n`;
                if (auditInfo.person) {
                    formattedInfo += `Person: ${auditInfo.person}\n`;
                }
                if (auditInfo.period) {
                    formattedInfo += `Period: ${auditInfo.period}\n`;
                }
                if (auditInfo.lender_amount) {
                    formattedInfo += `Lender Amount: ${auditInfo.lender_amount}\n`;
                }
                if (auditInfo.borrower_amount) {
                    formattedInfo += `Borrower Amount: ${auditInfo.borrower_amount}\n`;
                }
                if (auditInfo.jaccard_score !== undefined) {
                    formattedInfo += `Similarity: ${(auditInfo.jaccard_score * 100).toFixed(1)}%\n`;
                }
                break;
            case 'FINAL_SETTLEMENT':
                formattedInfo += `Final Settlement Match\n`;
                if (auditInfo.person) {
                    formattedInfo += `Person: ${auditInfo.person}\n`;
                }
                if (auditInfo.lender_amount) {
                    formattedInfo += `Lender Amount: ${auditInfo.lender_amount}\n`;
                }
                if (auditInfo.borrower_amount) {
                    formattedInfo += `Borrower Amount: ${auditInfo.borrower_amount}\n`;
                }
                break;
            case 'COMMON_TEXT':
                formattedInfo += `Common Text Match\n`;
                // Get the actual matched text from any field that might have it
                const matchedText = auditInfo.common_text || auditInfo.matched_text || auditInfo.matched_phrase || auditInfo.keywords || '';
                if (matchedText) {
                    formattedInfo += `Matched Text: ${matchedText}\n`;
                }
                if (auditInfo.lender_amount) {
                    formattedInfo += `Lender Amount: ${auditInfo.lender_amount}\n`;
                }
                if (auditInfo.borrower_amount) {
                    formattedInfo += `Borrower Amount: ${auditInfo.borrower_amount}\n`;
                }
                if (auditInfo.jaccard_score !== undefined) {
                    formattedInfo += `Similarity: ${(auditInfo.jaccard_score * 100).toFixed(1)}%\n`;
                }
                break;
            case 'INTERUNIT_LOAN':
                formattedInfo += `Interunit Loan Match\n`;
                if (auditInfo.lender_reference) {
                    formattedInfo += `Lender: ${auditInfo.lender_reference}\n`;
                }
                if (auditInfo.borrower_reference) {
                    formattedInfo += `Borrower: ${auditInfo.borrower_reference}\n`;
                }
                if (auditInfo.lender_amount) {
                    formattedInfo += `Lender Amount: ${auditInfo.lender_amount}\n`;
                }
                if (auditInfo.borrower_amount) {
                    formattedInfo += `Borrower Amount: ${auditInfo.borrower_amount}\n`;
                }
                break;
            default:
                formattedInfo += `Type: ${auditInfo.match_type}\n`;
                if (auditInfo.keywords) {
                    formattedInfo += `Keywords: ${auditInfo.keywords}\n`;
                }
                if (auditInfo.lender_amount) {
                    formattedInfo += `Lender Amount: ${auditInfo.lender_amount}\n`;
                }
                if (auditInfo.borrower_amount) {
                    formattedInfo += `Borrower Amount: ${auditInfo.borrower_amount}\n`;
                }
        }
        
        return formattedInfo.trim().replace(/^\n+/, '');
    } catch (e) {
        console.error('Error parsing audit info:', e);
        return auditInfoStr;
    }
}

// Function to deduplicate matches and show only unique matches
function deduplicateMatches(matches) {
    const uniqueMatches = [];
    const processedPairs = new Set();
    
    matches.forEach(match => {
        // Create a unique key for each match pair
        const uid1 = match.uid;
        const uid2 = match.matched_uid;
        const pairKey1 = `${uid1}-${uid2}`;
        const pairKey2 = `${uid2}-${uid1}`;
        
        // Check if we've already processed this pair
        if (!processedPairs.has(pairKey1) && !processedPairs.has(pairKey2)) {
            uniqueMatches.push(match);
            processedPairs.add(pairKey1);
            processedPairs.add(pairKey2);
        }
    });
    
    return uniqueMatches;
}

function displayMatches(matches, targetDivId = 'reconciliation-result', filterContext = null) {
    const resultDiv = document.getElementById(targetDivId);
    
    if (!matches || matches.length === 0) {
        // Check if we're in the matched results display
        if (targetDivId === 'matched-results-display') {
            resultDiv.innerHTML = `
                <div class="alert alert-info text-center">
                    <i class="bi bi-info-circle me-2"></i>No matches found for the selected company pair and period. 
                    <br>Try selecting different options or run reconciliation first.
                </div>
            `;
        } else {
        resultDiv.innerHTML = `
            <div class="alert alert-info text-center">
                <i class="bi bi-info-circle me-2"></i>No matches found. Run reconciliation to find matching transactions.
            </div>
        `;
        }
        return;
    }
    
    // Deduplicate matches to show only unique matches
    const uniqueMatches = deduplicateMatches(matches);
    
    // Sort matches: AUTO-MATCH records first, then others
    uniqueMatches.sort((a, b) => {
        // Parse audit info to get match type
        let matchTypeA = '';
        let matchTypeB = '';
        
        try {
            if (a.audit_info) {
                const auditInfoA = JSON.parse(a.audit_info);
                matchTypeA = auditInfoA.match_type || '';
            }
        } catch (e) {
            console.warn('Could not parse audit_info for record A:', a.audit_info);
        }
        
        try {
            if (b.audit_info) {
                const auditInfoB = JSON.parse(b.audit_info);
                matchTypeB = auditInfoB.match_type || '';
            }
        } catch (e) {
            console.warn('Could not parse audit_info for record B:', b.audit_info);
        }
        
        // Check if records are auto-accepted (PO, LC, LOAN_ID, FINAL_SETTLEMENT, or INTERUNIT_LOAN)
        const isAutoAcceptedA = ['PO', 'LC', 'LOAN_ID', 'FINAL_SETTLEMENT', 'INTERUNIT_LOAN'].includes(matchTypeA);
        const isAutoAcceptedB = ['PO', 'LC', 'LOAN_ID', 'FINAL_SETTLEMENT', 'INTERUNIT_LOAN'].includes(matchTypeB);
        
        // Sort: AUTO-MATCH records first (-1), then others (1)
        if (isAutoAcceptedA && !isAutoAcceptedB) {
            return -1; // A is AUTO-MATCH, B is not
        } else if (!isAutoAcceptedA && isAutoAcceptedB) {
            return 1; // A is not AUTO-MATCH, B is
        } else {
            return 0; // Both are same type, maintain original order
        }
    });
    
    // Get dynamic lender/borrower names from the first match (same logic as Excel export)
    let lender_name = 'Lender';
    let borrower_name = 'Borrower';
    if (uniqueMatches.length > 0) {
        const first_match = uniqueMatches[0];
        // Determine which is lender (Debit side) vs borrower (Credit side)
        if (first_match.Debit && first_match.Debit > 0) {
            // Main record is lender (Debit side)
            lender_name = first_match.lender || 'Lender';
            borrower_name = first_match.matched_lender || 'Borrower';
        } else if (first_match.matched_Debit && first_match.matched_Debit > 0) {
            // Matched record is lender (Debit side)
            lender_name = first_match.matched_lender || 'Lender';
            borrower_name = first_match.lender || 'Borrower';
        } else {
            // Fallback to original logic
            if (first_match.lender) {
                lender_name = first_match.lender;
            }
            if (first_match.matched_lender && first_match.matched_lender !== first_match.lender) {
                borrower_name = first_match.matched_lender;
            } else if (first_match.borrower) {
                borrower_name = first_match.borrower;
            }
        }
    }
    
    // Build context header if filter context is provided
    let contextHeader = '';
    if (filterContext && (filterContext.lenderCompany || filterContext.month)) {
        let filterInfo = [];
        if (filterContext.lenderCompany) {
            filterInfo.push(`<strong>Company Pair:</strong> ${filterContext.lenderCompany} ↔ ${filterContext.borrowerCompany}`);
        }
        if (filterContext.month) {
            filterInfo.push(`<strong>Statement Period:</strong> ${filterContext.month} ${filterContext.year}`);
        }
        
        if (filterInfo.length > 0) {
            contextHeader = `
                <div class="alert alert-primary mb-3" role="alert">
                    <i class="bi bi-funnel me-2"></i>${filterInfo.join('&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;')}
                </div>
            `;
        }
    }
    
    let tableHTML = `
        <div class="matched-transactions-wrapper">
            ${contextHeader}
            <div class="matched-header">
                <h6><i class="bi bi-link-45deg"></i> Matched Transactions (${uniqueMatches.length} transactions)</h6>
            </div>
            <div class="table-responsive">
                <table class="matched-transactions-table">
                <thead>
                    <tr>
                            <!-- Lender Columns -->
                            <th data-column="lender_uid">Lender UID</th>
                            <th data-column="lender_date">Lender Date</th>
                            <th data-column="lender_particulars">Lender Particulars</th>
                            <th data-column="lender_debit">Lender Debit</th>
                            <th data-column="lender_vch_type">Lender Vch Type</th>
                            <th data-column="lender_role">Lender Role</th>
                            <!-- Borrower Columns -->
                            <th data-column="borrower_uid">Borrower UID</th>
                            <th data-column="borrower_date">Borrower Date</th>
                            <th data-column="borrower_particulars">Borrower Particulars</th>
                            <th data-column="borrower_credit">Borrower Credit</th>
                            <th data-column="borrower_vch_type">Borrower Vch Type</th>
                            <th data-column="borrower_role">Borrower Role</th>
                            <!-- Match Details Columns -->
                            <th data-column="match_method">Match Method</th>
                            <th data-column="audit_info">Audit Info</th>
                            <th data-column="actions">Actions</th>
                    </tr>
                </thead>
                <tbody>
    `;
    
    uniqueMatches.forEach(match => {
        // Determine which record is lender and which is borrower based on Debit/Credit values
        let lenderRecord, borrowerRecord, lenderUid, borrowerUid, lenderRole, borrowerRole;
        
        // Check which record has Debit > 0 (Lender) vs Credit > 0 (Borrower)
        const main_record_debit = parseFloat(match.Debit || 0);
        const main_record_credit = parseFloat(match.Credit || 0);
        const matched_record_debit = parseFloat(match.matched_Debit || 0);
        const matched_record_credit = parseFloat(match.matched_Credit || 0);
        
        if (main_record_debit > 0) {
            // Main record is Lender (Debit > 0)
            lenderRecord = {
                Date: match.Date,
                Particulars: match.Particulars,
                Credit: match.Credit,
                Debit: match.Debit,
                Vch_Type: match.Vch_Type
            };
            lenderUid = match.uid;
            lenderRole = 'Lender'; // Correct - Debit > 0 = Lender
            
            borrowerRecord = {
                Date: match.matched_date,
                Particulars: match.matched_particulars,
                Credit: match.matched_Credit,
                Debit: match.matched_Debit,
                Vch_Type: match.matched_Vch_Type
            };
            borrowerUid = match.matched_uid;
            borrowerRole = 'Borrower'; // Correct - Credit > 0 = Borrower
        } else if (matched_record_debit > 0) {
            // Matched record is Lender (Debit > 0)
            lenderRecord = {
                Date: match.matched_date,
                Particulars: match.matched_particulars,
                Credit: match.matched_Credit,
                Debit: match.matched_Debit,
                Vch_Type: match.matched_Vch_Type
            };
            lenderUid = match.matched_uid;
            lenderRole = 'Lender'; // Correct - Debit > 0 = Lender
            
            borrowerRecord = {
                Date: match.Date,
                Particulars: match.Particulars,
                Credit: match.Credit,
                Debit: match.Debit,
                Vch_Type: match.Vch_Type
            };
            borrowerUid = match.uid;
            borrowerRole = 'Borrower'; // Correct - Credit > 0 = Borrower
        } else {
            // Fallback: use the original logic based on lender_name
            if (match.lender === lender_name) {
                lenderRecord = {
                    Date: match.Date,
                    Particulars: match.Particulars,
                    Credit: match.Credit,
                    Debit: match.Debit,
                    Vch_Type: match.Vch_Type
                };
                lenderUid = match.uid;
                // Determine role based on Debit/Credit
                lenderRole = (parseFloat(match.Debit || 0) > 0) ? 'Lender' : 'Borrower';
                
                borrowerRecord = {
                    Date: match.matched_date,
                    Particulars: match.matched_particulars,
                    Credit: match.matched_Credit,
                    Debit: match.matched_Debit,
                    Vch_Type: match.matched_Vch_Type
                };
                borrowerUid = match.matched_uid;
                // Determine role based on Debit/Credit
                borrowerRole = (parseFloat(match.matched_Debit || 0) > 0) ? 'Lender' : 'Borrower';
            } else {
                borrowerRecord = {
                    Date: match.Date,
                    Particulars: match.Particulars,
                    Credit: match.Credit,
                    Debit: match.Debit,
                    Vch_Type: match.Vch_Type
                };
                borrowerUid = match.uid;
                // Determine role based on Debit/Credit
                borrowerRole = (parseFloat(match.Debit || 0) > 0) ? 'Lender' : 'Borrower';
                
                lenderRecord = {
                    Date: match.matched_date,
                    Particulars: match.matched_particulars,
                    Credit: match.matched_Credit,
                    Debit: match.matched_Debit,
                    Vch_Type: match.matched_Vch_Type
                };
                lenderUid = match.matched_uid;
                // Determine role based on Debit/Credit
                lenderRole = (parseFloat(match.matched_Debit || 0) > 0) ? 'Lender' : 'Borrower';
            }
        }
        
        // Calculate the matched amount
        const matchedAmount = Math.max(
            parseFloat(lenderRecord.Debit || 0),
            parseFloat(lenderRecord.Credit || 0),
            parseFloat(borrowerRecord.Debit || 0),
            parseFloat(borrowerRecord.Credit || 0)
        );
        
        tableHTML += `
            <tr class="match-row">
                <!-- Lender Columns -->
                <td data-column="lender_uid" class="uid-cell">${lenderUid || ''}</td>
                <td data-column="lender_date">${formatDate(lenderRecord.Date)}</td>
                <td data-column="lender_particulars" class="particulars-cell table-cell-large">${lenderRecord.Particulars || ''}</td>
                <td data-column="lender_debit" class="amount-cell debit-amount">${formatAmount(lenderRecord.Debit || 0)}</td>
                <td data-column="lender_vch_type">${lenderRecord.Vch_Type || ''}</td>
                <td data-column="lender_role"><span class="role-badge lender-role">${lenderRole}</span></td>
                <!-- Borrower Columns -->
                <td data-column="borrower_uid" class="uid-cell">${borrowerUid || ''}</td>
                <td data-column="borrower_date">${formatDate(borrowerRecord.Date)}</td>
                <td data-column="borrower_particulars" class="particulars-cell table-cell-large">${borrowerRecord.Particulars || ''}</td>
                <td data-column="borrower_credit" class="amount-cell credit-amount">${formatAmount(borrowerRecord.Credit || 0)}</td>
                <td data-column="borrower_vch_type">${borrowerRecord.Vch_Type || ''}</td>
                <td data-column="borrower_role"><span class="role-badge borrower-role">${borrowerRole}</span></td>
                <!-- Match Details Columns -->
                <td data-column="match_method">${formatMatchMethod(match.match_method)}</td>
                <td data-column="audit_info">
                    <div class="audit-info-text">${(formatAuditInfo(match.audit_info) || '').replace(/\n/g, '<br>')}</div>
                </td>
                <td data-column="actions">
                    ${generateActionButtons(match)}
                </td>
            </tr>
        `;
    });
    
    tableHTML += `
                </tbody>
            </table>
            </div>
        </div>
    `;
    
    resultDiv.innerHTML = tableHTML;
}

// Generate action buttons based on match type and status
function generateActionButtons(match) {
    // Parse audit info to get match type
    let matchType = '';
    try {
        if (match.audit_info) {
            const auditInfo = JSON.parse(match.audit_info);
            matchType = auditInfo.match_type || '';
        }
    } catch (e) {
        console.warn('Could not parse audit_info:', match.audit_info);
    }
    
    // Check if this match is auto-accepted (PO, LC, LOAN_ID, FINAL_SETTLEMENT, or INTERUNIT_LOAN)
    const isAutoAccepted = ['PO', 'LC', 'LOAN_ID', 'FINAL_SETTLEMENT', 'INTERUNIT_LOAN'].includes(matchType);
    
    // If auto-accepted, show a badge instead of action buttons
    if (isAutoAccepted) {
        return `
            <div class="d-flex justify-content-center align-items-center">
                <span class="badge bg-success text-white px-2 py-2" style="font-size: 10px;">
                    <i class="bi bi-check-circle me-1"></i>Auto-Match
                </span>
            </div>
        `;
    }
    
    // For other match types, show the action buttons
    return `
        <div class="btn-group" role="group" aria-label="Match actions">
            <button class="btn btn-outline-success btn-sm" onclick="acceptMatch('${match.uid}')" title="Accept Match">
                ✔
            </button>
            <button class="btn btn-outline-danger btn-sm" onclick="rejectMatch('${match.uid}')" title="Reject Match">
                ✖
            </button>
        </div>
    `;
}

// Accept/Reject functions
async function acceptMatch(uid) {
    try {
        const response = await fetch('/api/accept-match', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                uid: uid,
                confirmed_by: 'User'
            })
        });
        
        const result = await response.json();
        
        if (response.ok) {
            showNotification('Match accepted successfully!', 'success');
            loadMatches(); // Refresh the matches display
        } else {
            showNotification(`Failed to accept match: ${result.error}`, 'error');
        }
        
    } catch (error) {
        showNotification(`Error accepting match: ${error.message}`, 'error');
    }
}

async function rejectMatch(uid) {
    if (!confirm('Are you sure you want to reject this match?')) {
        return;
    }
    
    try {
        const response = await fetch('/api/reject-match', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                uid: uid,
                confirmed_by: 'User'
            })
        });
        
        const result = await response.json();
        
        if (response.ok) {
            showNotification('Match rejected successfully!', 'success');
            loadMatches(); // Refresh the matches display
        } else {
            showNotification(`Failed to reject match: ${result.error}`, 'error');
        }
        
    } catch (error) {
        showNotification(`Error rejecting match: ${error.message}`, 'error');
    }
}

// Utility functions
function formatDate(dateString) {
    if (!dateString) return '';
    try {
        // Try parsing as ISO date first
        let date;
        if (typeof dateString === 'string' && dateString.includes('-')) {
            const [year, month, day] = dateString.split('-');
            date = new Date(year, parseInt(month) - 1, day);
        } else {
            date = new Date(dateString);
        }
        
        if (isNaN(date.getTime())) {
            throw new Error('Invalid date');
        }
        
        const year = date.getFullYear();
        const month = String(date.getMonth() + 1).padStart(2, '0');
        const day = String(date.getDate()).padStart(2, '0');
        return `${year}-${month}-${day}`;
    } catch {
        // If parsing fails, try to extract date components from string
        const datePattern = /(\d{4})-(\d{2})-(\d{2})|(\d{2})[-/](\d{2})[-/](\d{4})|(\d{2})[-/](\d{2})[-/](\d{2})/;
        const match = dateString.toString().match(datePattern);
        if (match) {
            if (match[1]) { // YYYY-MM-DD
                return `${match[1]}-${match[2]}-${match[3]}`;
            } else if (match[4]) { // DD-MM-YYYY or DD/MM/YYYY
                return `${match[6]}-${match[5]}-${match[4]}`;
            } else if (match[7]) { // DD-MM-YY or DD/MM/YY
                const year = parseInt(match[9]) < 50 ? '20' + match[9] : '19' + match[9];
                return `${year}-${match[8]}-${match[7]}`;
            }
        }
        return dateString;
    }
}

function formatAmount(amount) {
    if (!amount || amount === '') return '';
    try {
        return parseFloat(amount).toLocaleString('en-IN', {
            minimumFractionDigits: 2,
            maximumFractionDigits: 2
        });
    } catch {
        return amount;
    }
} 

// Fetch and display recent uploads
async function loadRecentUploads() {
    try {
        const response = await fetch('/api/recent-uploads');
        const result = await response.json();
        const container = document.getElementById('recent-uploads-list');
        if (response.ok && result.recent_uploads && result.recent_uploads.length > 0) {
            let html = '<div class="upload-history">';
            html += '<h6 class="mb-3"><i class="bi bi-clock-history me-2"></i>File Upload History</h6>';
            
            // Display uploads in reverse chronological order (newest first)
            result.recent_uploads.slice().reverse().forEach((upload, index) => {
                html += '<div class="alert alert-success mb-2" role="alert">';
                html += '<div class="d-flex align-items-center">';
                html += '<i class="bi bi-file-earmark-arrow-up me-2"></i>';
                
                // Check if this is a file pair (contains " AND ")
                if (upload.includes(' AND ')) {
                    const [file1, file2] = upload.split(' AND ');
                    const pairHtml = '<span><strong>Files:</strong></span><span>&nbsp;</span>' + file1 + ' <span class="and-button"><strong>AND</strong></span> ' + file2;
                    html += pairHtml;
                } else {
                    // Handle legacy individual files
                    html += '<strong>File: </strong>' + upload;
                }
                
                html += '</div>';
                html += '</div>';
            });
            
            html += '</div>';
            container.innerHTML = html;
        } else {
            container.innerHTML = '';
        }
    } catch (error) {
        document.getElementById('recent-uploads-list').innerHTML = '';
    }
}

// Add Clear File List button handler
async function clearRecentUploads() {
    try {
        const response = await fetch('/api/clear-recent-uploads', { method: 'POST' });
        if (response.ok) {
            loadRecentUploads();
        }
    } catch (error) {
        // Ignore
    }
}

// Function to remove a specific upload from history
async function removeUploadFromHistory(index) {
    try {
        const response = await fetch('/api/remove-upload-from-history', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ index: index })
        });
        if (response.ok) {
            loadRecentUploads();
        }
    } catch (error) {
        // Ignore
    }
}

// Load detected company pairs
async function loadDetectedPairs() {
    try {
        const response = await fetch('/api/detected-pairs');
        const result = await response.json();
        
        if (response.ok) {
            displayDetectedPairs(result.pairs, 'Smart Scan');
        } else {
            console.error('Failed to load detected pairs:', result.error);
        }
    } catch (error) {
        console.error('Error loading detected pairs:', error);
    }
}

async function loadManualPairs() {
    try {
        const response = await fetch('/api/manual-pairs');
        const result = await response.json();
        
        if (response.ok) {
            displayDetectedPairs(result.pairs, 'Manual Pairs');
        } else {
            console.error('Failed to load manual pairs:', result.error);
        }
    } catch (error) {
        console.error('Error loading manual pairs:', error);
    }
}

function displayDetectedPairs(pairs, type) {
    const displayDiv = document.getElementById('detected-pairs-display');
    
    if (!pairs || pairs.length === 0) {
        displayDiv.innerHTML = `
            <div class="alert alert-info text-center">
                <i class="bi bi-info-circle me-2"></i>No ${type.toLowerCase()} pairs found.
            </div>
        `;
        return;
    }
    
    let html = `
        <div class="card">
            <div class="card-header">
                <h6 class="mb-0"><i class="bi bi-diagram-3 me-2"></i>${type} Results (${pairs.length} pairs)</h6>
            </div>
            <div class="card-body">
                <div class="table-responsive">
                    <table class="table table-sm">
                        <thead>
                            <tr>
                                <th>Company Pair</th>
                                <th>Period</th>
                                <th>Transactions</th>
                                <th>Type</th>
                            </tr>
                        </thead>
                        <tbody>
    `;
    
    pairs.forEach(pair => {
        const description = pair.description || `${pair.lender_company} ↔ ${pair.borrower_company}`;
        const period = `${pair.month} ${pair.year}`;
        const transactionCount = pair.transaction_count || 'N/A';
        const pairType = pair.type || 'detected';
        
        html += `
            <tr>
                <td><strong>${description}</strong></td>
                <td>${period}</td>
                <td><span class="badge bg-info">${transactionCount}</span></td>
                <td><span class="badge bg-secondary">${pairType}</span></td>
            </tr>
        `;
        
        // If this pair has an opposite pair, show it too
        if (pair.opposite_pair) {
            const oppositeDescription = pair.opposite_pair.description;
            html += `
                <tr>
                    <td style="padding-left: 20px;"><em>${oppositeDescription}</em></td>
                    <td>${period}</td>
                    <td><span class="badge bg-info">${transactionCount}</span></td>
                    <td><span class="badge bg-secondary">${pairType}</span></td>
                </tr>
            `;
        }
    });
    
    html += `
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
    `;
    
    displayDiv.innerHTML = html;
} 

// Load and display pairs
async function loadPairs() {
    try {
        const response = await fetch('/api/pairs');
        const result = await response.json();
        
        if (response.ok) {
            displayPairs(result.pairs);
        } else {
            console.error('Failed to load pairs:', result.error);
        }
    } catch (error) {
        console.error('Error loading pairs:', error);
    }
}

function displayPairs(pairs) {
    const resultDiv = document.getElementById('pairs-table-result');
    
    if (!pairs || pairs.length === 0) {
        resultDiv.innerHTML = `
            <div class="alert alert-info text-center">
                <i class="bi bi-info-circle me-2"></i>No upload pairs found. Upload some files to get started.
            </div>
        `;
        return;
    }
    
    let tableHTML = `
        <div class="table-responsive">
            <table class="table table-striped table-hover">
                <thead>
                    <tr>
                        <th data-column="pair_id" class="uid-cell text-center">Pair ID</th>
                        <th data-column="upload_date" class="date-cell text-center">Upload Date</th>
                        <th data-column="record_count" class="amount-cell text-center">Records</th>
                        <th data-column="actions" class="text-center">Actions</th>
                    </tr>
                </thead>
                <tbody>
    `;
    
    pairs.forEach(pair => {
        // Handle date formatting with error checking
        let uploadDate = 'Invalid Date';
        try {
            if (pair.upload_date) {
                const date = new Date(pair.upload_date);
                if (!isNaN(date.getTime())) {
                    uploadDate = date.toLocaleString();
                }
            }
        } catch (e) {
            console.warn('Error formatting date:', e);
        }
        
        // Handle record count with fallback
        const recordCount = pair.record_count || 0;
        
        // Handle pair_id with fallback
        const pairId = pair.pair_id || 'Unknown';
        
        tableHTML += `
            <tr>
                <td data-column="pair_id" class="uid-cell"><code>${pairId}</code></td>
                <td data-column="upload_date" class="date-cell">${uploadDate}</td>
                <td data-column="record_count" class="amount-cell"><span class="badge bg-info">${recordCount}</span></td>
                <td data-column="actions">
                    <a href="#" onclick="viewPairData('${pairId}')" class="text-primary text-decoration-none">
                        <i class="bi bi-eye"></i> View
                    </a>
                </td>
            </tr>
        `;
    });
    
    tableHTML += `
                </tbody>
            </table>
        </div>
    `;
    
    resultDiv.innerHTML = tableHTML;
}

async function viewPairData(pairId) {
    try {
        const response = await fetch(`/api/pair/${pairId}/data`);
        const result = await response.json();
        
        if (response.ok) {
            // Switch to data table tab and display the pair data
            showTab('data-table');
            displayData(result.data, null);
            
            // Show which pair is being viewed
            const resultDiv = document.getElementById('data-table-result');
            resultDiv.innerHTML = `
                <div class="alert alert-info">
                    <strong>Viewing Pair:</strong> ${pairId}
                </div>
                ${resultDiv.innerHTML}
            `;
        } else {
            showNotification(`Failed to load pair data: ${result.error}`, 'error');
        }
    } catch (error) {
        showNotification(`Error loading pair data: ${error.message}`, 'error');
    }
}

 

// Load unmatched results
async function loadUnmatchedResults() {
    const resultDiv = document.getElementById('unmatched-results-display');
    resultDiv.innerHTML = '<div class="alert alert-info"><i class="bi bi-info-circle me-2"></i>Loading unmatched results...</div>';
    
    // Get selected company pair and period
    const companySelect = document.getElementById('unmatched-company-pair-select');
    const periodSelect = document.getElementById('unmatched-period-select');
    const companyPair = companySelect ? companySelect.value : '';
    const period = periodSelect ? periodSelect.value : '';
    
    let lenderCompany = '';
    let borrowerCompany = '';
    let month = '';
    let year = '';
    
    if (companyPair && companyPair.includes('↔')) {
        const parts = companyPair.split('↔').map(s => s.trim());
        lenderCompany = parts[0];
        borrowerCompany = parts[1];
    }
    
    if (period && period !== '-- All Periods --') {
        const periodParts = period.split(' ');
        if (periodParts.length === 2) {
            month = periodParts[0];
            year = periodParts[1];
        }
    }
    
    // Build query string
        let url = '/api/unmatched';
    const params = [];
    if (lenderCompany && borrowerCompany) {
        params.push(`lender_company=${encodeURIComponent(lenderCompany)}`);
        params.push(`borrower_company=${encodeURIComponent(borrowerCompany)}`);
    }
    if (month) params.push(`month=${encodeURIComponent(month)}`);
    if (year) params.push(`year=${encodeURIComponent(year)}`);
    if (params.length > 0) {
        url += '?' + params.join('&');
    }
    
    try {
        const response = await fetch(url);
        const result = await response.json();
        
        if (response.ok) {
            // Pass filter context to displayUnmatchedResults for context header
            const filterContext = {
                lenderCompany: lenderCompany,
                borrowerCompany: borrowerCompany,
                month: month,
                year: year
            };
            displayUnmatchedResults(result.unmatched, filterContext);
        } else {
            resultDiv.innerHTML = `<div class="alert alert-danger"><i class="bi bi-exclamation-circle me-2"></i>Failed to load unmatched results: ${result.error}</div>`;
        }
    } catch (error) {
        resultDiv.innerHTML = `<div class="alert alert-danger"><i class="bi bi-exclamation-circle me-2"></i>Failed to load unmatched results: ${error.message}</div>`;
    }
}

// Download unmatched results
async function downloadUnmatchedResults() {
    try {
        // Get selected company pair and period
        const companySelect = document.getElementById('unmatched-company-pair-select');
        const periodSelect = document.getElementById('unmatched-period-select');
        const companyPair = companySelect ? companySelect.value : '';
        const period = periodSelect ? periodSelect.value : '';
        
        let lenderCompany = '';
        let borrowerCompany = '';
        let month = '';
        let year = '';
        
        if (companyPair && companyPair.includes('↔')) {
            const parts = companyPair.split('↔').map(s => s.trim());
            lenderCompany = parts[0];
            borrowerCompany = parts[1];
        }
        
        if (period && period !== '-- All Periods --') {
            const periodParts = period.split(' ');
            if (periodParts.length === 2) {
                month = periodParts[0];
                year = periodParts[1];
            }
        }
        
        // Build query string
        let url = '/api/download-unmatched';
        const params = [];
        if (lenderCompany && borrowerCompany) {
            params.push(`lender_company=${encodeURIComponent(lenderCompany)}`);
            params.push(`borrower_company=${encodeURIComponent(borrowerCompany)}`);
        }
        if (month) params.push(`month=${encodeURIComponent(month)}`);
        if (year) params.push(`year=${encodeURIComponent(year)}`);
        if (params.length > 0) {
            url += '?' + params.join('&');
        }
        
        window.location.href = url;
    } catch (error) {
        console.error('Error downloading unmatched results:', error);
    }
}

// Display unmatched results
function displayUnmatchedResults(unmatched, filterContext = null) {
    const displayDiv = document.getElementById('unmatched-results-display');
    
    if (!unmatched || unmatched.length === 0) {
        displayDiv.innerHTML = `
            <div class="alert alert-info text-center">
                <i class="bi bi-info-circle me-2"></i>No unmatched transactions found for the selected company pair and period. 
                <br>Try selecting different options or check if data exists for this combination.
            </div>
        `;
        return;
    }
    
    // Build context header if filter context is provided
    let contextHeader = '';
    if (filterContext && (filterContext.lenderCompany || filterContext.month)) {
        let filterInfo = [];
        if (filterContext.lenderCompany) {
            filterInfo.push(`<strong>Company Pair:</strong> ${filterContext.lenderCompany} ↔ ${filterContext.borrowerCompany}`);
        }
        if (filterContext.month) {
            filterInfo.push(`<strong>Statement Period:</strong> ${filterContext.month} ${filterContext.year}`);
        }
        
        if (filterInfo.length > 0) {
            contextHeader = `
                <div class="alert alert-primary mb-3" role="alert">
                    <i class="bi bi-funnel me-2"></i>${filterInfo.join('&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;')}
                </div>
            `;
        }
    }
    
    let tableHTML = `
        <div class="unmatched-transactions-wrapper">
            ${contextHeader}
            <div class="unmatched-header">
                <h6><i class="bi bi-link-45deg"></i> Unmatched Transactions (${unmatched.length} records)</h6>
            </div>
            <div class="table-responsive">
                <table class="unmatched-transactions-table">
                    <thead>
                        <tr>
                            <th data-column="uid" class="uid-cell text-center">UID</th>
                            <th data-column="lender" class="lender-cell text-center">Lender</th>
                            <th data-column="borrower" class="borrower-cell text-center">Borrower</th>
                            <th data-column="statement_month" class="statement-month-cell text-center">Statement Month</th>
                            <th data-column="statement_year" class="statement-year-cell text-center">Statement Year</th>
                            <th data-column="date" class="date-cell text-center">Date</th>
                            <th data-column="particulars" class="particulars-cell text-center">Particulars</th>
                            <th data-column="vch_type" class="vch-type-cell text-center">Voucher Type</th>
                            <th data-column="vch_no" class="vch-no-cell text-center">Voucher No</th>
                            <th data-column="debit" class="amount-cell text-center">Debit Amount</th>
                            <th data-column="credit" class="amount-cell text-center">Credit Amount</th>
                            <th data-column="entered_by" class="entered-by-cell text-center">Entered By</th>
                            <th data-column="input_date" class="input-date-cell text-center">Input Date</th>
                            <th data-column="role" class="role-cell text-center">Role</th>
                        </tr>
                    </thead>
                    <tbody>
    `;
    
    unmatched.forEach(record => {
        tableHTML += `
            <tr>
                <td data-column="uid" class="uid-cell">${record.uid || ''}</td>
                <td data-column="lender" class="lender-cell">${record.lender || ''}</td>
                <td data-column="borrower" class="borrower-cell">${record.borrower || ''}</td>
                <td data-column="statement_month" class="statement-month-cell">${record.statement_month || ''}</td>
                <td data-column="statement_year" class="statement-year-cell">${record.statement_year || ''}</td>
                <td data-column="date" class="date-cell">${formatDate(record.Date) || ''}</td>
                <td data-column="particulars" class="particulars-cell">${record.Particulars || ''}</td>
                <td data-column="vch_type" class="vch-type-cell">${record.Vch_Type || ''}</td>
                <td data-column="vch_no" class="vch-no-cell">${record.Vch_No || ''}</td>
                <td data-column="debit" class="amount-cell text-end">${formatAmount(record.Debit || '')}</td>
                <td data-column="credit" class="amount-cell text-end">${formatAmount(record.Credit || '')}</td>
                <td data-column="entered_by" class="entered-by-cell">${record.entered_by || ''}</td>
                <td data-column="input_date" class="input-date-cell">${formatDate(record.input_date) || ''}</td>
                <td data-column="role" class="role-cell">${record.role || ''}</td>
            </tr>
        `;
    });
    
    tableHTML += `
                    </tbody>
                </table>
            </div>
        </div>
    `;
    
    displayDiv.innerHTML = tableHTML;
}

// Load company pairs for unmatched filter
async function loadUnmatchedCompanyPairs() {
    try {
        const response = await fetch('/api/detected-pairs');
        const result = await response.json();
        
        if (response.ok && result.pairs) {
            const select = document.getElementById('unmatched-company-pair-select');
            const periodSelect = document.getElementById('unmatched-period-select');
            
            // Clear existing options
            select.innerHTML = '<option value="">-- All Company Pairs --</option>';
            periodSelect.innerHTML = '<option value="">-- Select Statement Period --</option>';
            
            // Use Set to ensure unique company pairs
            const uniqueCompanyPairs = new Set();
            result.pairs.forEach(pair => {
                const lender = pair.lender_company || pair.current_company || '';
                const borrower = pair.borrower_company || pair.counterparty || '';
                const companyPair = `${lender} ↔ ${borrower}`;
                
                // Only add if it's a valid company pair (not empty)
                if (lender && borrower && lender !== borrower) {
                    uniqueCompanyPairs.add(companyPair);
                }
            });
            
            // Add unique company pairs to dropdown
            uniqueCompanyPairs.forEach(companyPair => {
                const option = document.createElement('option');
                option.value = companyPair;
                option.textContent = companyPair;
                select.appendChild(option);
            });
            
            // Add event listeners for button state and dynamic period filtering
            select.addEventListener('change', function() {
                updateUnmatchedPeriods(result.pairs);
                checkUnmatchedButtonState();
            });
            periodSelect.addEventListener('change', checkUnmatchedButtonState);
            
            // Initial button state check
            checkUnmatchedButtonState();
        }
    } catch (error) {
        console.error('Error loading company pairs:', error);
    }
}

function updateUnmatchedPeriods(allPairs) {
    const companySelect = document.getElementById('unmatched-company-pair-select');
    const periodSelect = document.getElementById('unmatched-period-select');
    const selectedCompanyPair = companySelect.value;
    
    // Clear existing periods
    periodSelect.innerHTML = '<option value="">-- Select Statement Period --</option>';
    
    if (!selectedCompanyPair || selectedCompanyPair === '-- All Company Pairs --') {
        // If no company pair selected, don't populate periods
        return;
    } else {
        // Filter periods for the selected company pair
        const [lender, borrower] = selectedCompanyPair.split(' ↔ ');
        const periods = new Set();
        
        allPairs.forEach(pair => {
            const pairLender = pair.lender_company || pair.current_company || '';
            const pairBorrower = pair.borrower_company || pair.counterparty || '';
            
            // Check if this pair matches the selected company pair
            if ((pairLender === lender && pairBorrower === borrower) || 
                (pairLender === borrower && pairBorrower === lender)) {
                const periodText = `${pair.month} ${pair.year}`;
                periods.add(periodText);
            }
        });
        
        // Sort and add filtered periods
        const sortedPeriods = Array.from(periods).sort((a, b) => {
            const [monthA, yearA] = a.split(' ');
            const [monthB, yearB] = b.split(' ');
            
            const monthNames = ['January', 'February', 'March', 'April', 'May', 'June', 
                              'July', 'August', 'September', 'October', 'November', 'December'];
            const monthAIndex = monthNames.indexOf(monthA);
            const monthBIndex = monthNames.indexOf(monthB);
            
            if (yearA !== yearB) {
                return parseInt(yearA) - parseInt(yearB);
            }
            return monthAIndex - monthBIndex;
        });
        
        sortedPeriods.forEach(periodText => {
            const periodOption = document.createElement('option');
            periodOption.value = periodText;
            periodOption.textContent = periodText;
            periodSelect.appendChild(periodOption);
        });
    }
}

function clearUnmatchedCompanySelection() {
    document.getElementById('unmatched-company-pair-select').value = '';
    document.getElementById('unmatched-period-select').value = '';
    checkUnmatchedButtonState();
}

// Load company pairs for matched filter
async function loadMatchedCompanyPairs() {
    try {
        const response = await fetch('/api/matched-pairs');
        const result = await response.json();
        
        if (response.ok && result.pairs) {
            const select = document.getElementById('matched-company-pair-select');
            const periodSelect = document.getElementById('matched-period-select');
            
            // Clear existing options
            select.innerHTML = '<option value="">-- All Company Pairs --</option>';
            periodSelect.innerHTML = '<option value="">-- Select Statement Period --</option>';
            
            // Use Set to ensure unique company pairs
            const uniqueCompanyPairs = new Set();
            result.pairs.forEach(pair => {
                const lender = pair.lender_company || pair.current_company || '';
                const borrower = pair.borrower_company || pair.counterparty || '';
                const companyPair = `${lender} ↔ ${borrower}`;
                
                // Only add if it's a valid company pair (not empty)
                if (lender && borrower && lender !== borrower) {
                    uniqueCompanyPairs.add(companyPair);
                }
            });
            
            // Add unique company pairs to dropdown
            uniqueCompanyPairs.forEach(companyPair => {
                const option = document.createElement('option');
                option.value = companyPair;
                option.textContent = companyPair;
                select.appendChild(option);
            });
            
            // Add event listeners for button state and dynamic period filtering
            select.addEventListener('change', function() {
                updateMatchedPeriods(result.pairs);
                checkMatchedButtonState();
            });
            periodSelect.addEventListener('change', checkMatchedButtonState);
            
            // Initial button state check
            checkMatchedButtonState();
        }
    } catch (error) {
        console.error('Error loading matched company pairs:', error);
    }
}

function updateMatchedPeriods(allPairs) {
    const companySelect = document.getElementById('matched-company-pair-select');
    const periodSelect = document.getElementById('matched-period-select');
    const selectedCompanyPair = companySelect.value;
    
    // Clear existing periods
    periodSelect.innerHTML = '<option value="">-- Select Statement Period --</option>';
    
    if (!selectedCompanyPair || selectedCompanyPair === '-- All Company Pairs --') {
        // If no company pair selected, don't populate periods
        return;
    } else {
        // Filter periods for the selected company pair
        const [lender, borrower] = selectedCompanyPair.split(' ↔ ');
        const periods = new Set();
        
        allPairs.forEach(pair => {
            const pairLender = pair.lender_company || pair.current_company || '';
            const pairBorrower = pair.borrower_company || pair.counterparty || '';
            
            // Check if this pair matches the selected company pair
            if ((pairLender === lender && pairBorrower === borrower) || 
                (pairLender === borrower && pairBorrower === lender)) {
                const periodText = `${pair.month} ${pair.year}`;
                periods.add(periodText);
            }
        });
        
        // Sort and add filtered periods
        const sortedPeriods = Array.from(periods).sort((a, b) => {
            const [monthA, yearA] = a.split(' ');
            const [monthB, yearB] = b.split(' ');
            
            const monthNames = ['January', 'February', 'March', 'April', 'May', 'June', 
                              'July', 'August', 'September', 'October', 'November', 'December'];
            const monthAIndex = monthNames.indexOf(monthA);
            const monthBIndex = monthNames.indexOf(monthB);
            
            if (yearA !== yearB) {
                return parseInt(yearA) - parseInt(yearB);
            }
            return monthAIndex - monthBIndex;
        });
        
        sortedPeriods.forEach(periodText => {
            const periodOption = document.createElement('option');
            periodOption.value = periodText;
            periodOption.textContent = periodText;
            periodSelect.appendChild(periodOption);
        });
    }
}

function clearMatchedCompanySelection() {
    document.getElementById('matched-company-pair-select').value = '';
    document.getElementById('matched-period-select').value = '';
    checkMatchedButtonState();
}

// Load company pairs for reconciliation filter
async function loadReconciliationCompanyPairs() {
    try {
        const response = await fetch('/api/unreconciled-pairs');
        const result = await response.json();
        
        if (response.ok && result.pairs) {
            const select = document.getElementById('reconciliation-company-pair-select');
            const periodSelect = document.getElementById('reconciliation-period-select');
            
            // Clear existing options
            select.innerHTML = '<option value="">-- Select Company Pair --</option>';
            periodSelect.innerHTML = '<option value="">-- Select Statement Period --</option>';
            
            // Use Set to ensure unique company pairs
            const uniqueCompanyPairs = new Set();
            result.pairs.forEach(pair => {
                const lender = pair.lender_company || pair.current_company || '';
                const borrower = pair.borrower_company || pair.counterparty || '';
                const companyPair = `${lender} ↔ ${borrower}`;
                
                // Only add if it's a valid company pair (not empty)
                if (lender && borrower && lender !== borrower) {
                    uniqueCompanyPairs.add(companyPair);
                }
            });
            
            // Add unique company pairs to dropdown
            uniqueCompanyPairs.forEach(companyPair => {
                const option = document.createElement('option');
                option.value = companyPair;
                option.textContent = companyPair;
                select.appendChild(option);
            });
            
            // Add event listeners for button state and dynamic period filtering
            select.addEventListener('change', function() {
                updateReconciliationPeriods(result.pairs);
                checkReconciliationButtonState();
            });
            periodSelect.addEventListener('change', checkReconciliationButtonState);
            
            // Initial button state check
            checkReconciliationButtonState();
        }
    } catch (error) {
        console.error('Error loading reconciliation company pairs:', error);
    }
}

function updateReconciliationPeriods(allPairs) {
    const companySelect = document.getElementById('reconciliation-company-pair-select');
    const periodSelect = document.getElementById('reconciliation-period-select');
    const selectedCompanyPair = companySelect.value;
    
    // Clear existing periods
    periodSelect.innerHTML = '<option value="">-- Select Statement Period --</option>';
    
    if (!selectedCompanyPair || selectedCompanyPair === '-- Select Company Pair --') {
        // If no company pair selected, don't populate periods
        return;
    } else {
        // Filter periods for the selected company pair
        const [lender, borrower] = selectedCompanyPair.split(' ↔ ');
        const periods = new Set();
        
        allPairs.forEach(pair => {
            const pairLender = pair.lender_company || pair.current_company || '';
            const pairBorrower = pair.borrower_company || pair.counterparty || '';
            
            // Check if this pair matches the selected company pair
            if ((pairLender === lender && pairBorrower === borrower) || 
                (pairLender === borrower && pairBorrower === lender)) {
                const periodText = `${pair.month} ${pair.year}`;
                periods.add(periodText);
            }
        });
        
        // Sort and add filtered periods
        const sortedPeriods = Array.from(periods).sort((a, b) => {
            const [monthA, yearA] = a.split(' ');
            const [monthB, yearB] = b.split(' ');
            
            const monthNames = ['January', 'February', 'March', 'April', 'May', 'June', 
                              'July', 'August', 'September', 'October', 'November', 'December'];
            const monthAIndex = monthNames.indexOf(monthA);
            const monthBIndex = monthNames.indexOf(monthB);
            
            if (yearA !== yearB) {
                return parseInt(yearA) - parseInt(yearB);
            }
            return monthAIndex - monthBIndex;
        });
        
        sortedPeriods.forEach(periodText => {
            const periodOption = document.createElement('option');
            periodOption.value = periodText;
            periodOption.textContent = periodText;
            periodSelect.appendChild(periodOption);
        });
    }
}

function clearReconciliationSelection() {
    document.getElementById('reconciliation-company-pair-select').value = '';
    document.getElementById('reconciliation-period-select').value = '';
    checkReconciliationButtonState();
}

function checkReconciliationButtonState() {
    const companySelect = document.getElementById('reconciliation-company-pair-select');
    const periodSelect = document.getElementById('reconciliation-period-select');
    const runButton = document.getElementById('run-reconciliation-btn');
    
    const companySelected = companySelect && companySelect.value && companySelect.value !== '-- Select Company Pair --';
    const periodSelected = periodSelect && periodSelect.value && periodSelect.value !== '-- Select Statement Period --';
    
    if (runButton) {
        if (companySelected && periodSelected) {
            runButton.disabled = false;
            runButton.classList.remove('btn-secondary');
            runButton.classList.add('btn-primary');
        } else {
            runButton.disabled = true;
            runButton.classList.remove('btn-primary');
            runButton.classList.add('btn-secondary');
        }
    }
}

function checkMatchedButtonState() {
    const companySelect = document.getElementById('matched-company-pair-select');
    const periodSelect = document.getElementById('matched-period-select');
    const viewButton = document.getElementById('view-matched-btn');
    const downloadButton = document.getElementById('download-matched-btn');
    
    const companySelected = companySelect && companySelect.value && companySelect.value !== '-- All Company Pairs --';
    const periodSelected = periodSelect && periodSelect.value && periodSelect.value !== '-- All Periods --';
    
    if (viewButton) {
        if (companySelected && periodSelected) {
            viewButton.disabled = false;
            viewButton.classList.remove('btn-secondary');
            viewButton.classList.add('btn-primary');
        } else {
            viewButton.disabled = true;
            viewButton.classList.remove('btn-primary');
            viewButton.classList.add('btn-secondary');
        }
    }
    
    if (downloadButton) {
        if (companySelected && periodSelected) {
            downloadButton.disabled = false;
            downloadButton.classList.remove('btn-secondary');
            downloadButton.classList.add('btn-success');
        } else {
            downloadButton.disabled = true;
            downloadButton.classList.remove('btn-success');
            downloadButton.classList.add('btn-secondary');
        }
    }
}

function checkUnmatchedButtonState() {
    const companySelect = document.getElementById('unmatched-company-pair-select');
    const periodSelect = document.getElementById('unmatched-period-select');
    const viewButton = document.getElementById('view-unmatched-btn');
    const downloadButton = document.getElementById('download-unmatched-btn');
    
    const companySelected = companySelect && companySelect.value && companySelect.value !== '-- All Company Pairs --';
    const periodSelected = periodSelect && periodSelect.value && periodSelect.value !== '-- All Periods --';
    
    if (viewButton) {
        if (companySelected && periodSelected) {
            viewButton.disabled = false;
            viewButton.classList.remove('btn-secondary');
            viewButton.classList.add('btn-primary');
        } else {
            viewButton.disabled = true;
            viewButton.classList.remove('btn-primary');
            viewButton.classList.add('btn-secondary');
        }
    }
    
    if (downloadButton) {
        if (companySelected && periodSelected) {
            downloadButton.disabled = false;
            downloadButton.classList.remove('btn-secondary');
            downloadButton.classList.add('btn-success');
        } else {
            downloadButton.disabled = true;
            downloadButton.classList.remove('btn-success');
            downloadButton.classList.add('btn-secondary');
        }
    }
}

// Global variable to store reconciliation history
let reconciliationHistory = [];

// Function to add reconciliation result to history
function addReconciliationToHistory(result) {
    reconciliationHistory.push(result);
    // Keep only the last 20 reconciliations to prevent the list from getting too long
    if (reconciliationHistory.length > 20) {
        reconciliationHistory = reconciliationHistory.slice(-20);
    }
}

// Function to display all reconciliation history
function displayReconciliationHistory() {
    const resultDiv = document.getElementById('reconciliation-result');
    if (!resultDiv) return;
    
    if (reconciliationHistory.length === 0) {
        resultDiv.innerHTML = '';
        return;
    }
    
    let historyHTML = '<div class="reconciliation-history">';
    historyHTML += '<h6 class="mb-3"><i class="bi bi-clock-history me-2"></i>Reconciliation History</h6>';
    
    // Display reconciliations in reverse chronological order (newest first)
    reconciliationHistory.slice().reverse().forEach((result, index) => {
        historyHTML += '<div class="alert alert-success mb-2" role="alert">';
        historyHTML += '<div class="d-flex justify-content-between align-items-start">';
        historyHTML += '<div class="flex-grow-1">';
        historyHTML += '<div class="d-flex align-items-center mb-1">';
        historyHTML += '<i class="bi bi-check-circle me-2"></i>';
        historyHTML += '<strong>Reconciliation Completed</strong>';
        historyHTML += '<small class="text-muted ms-2">' + result.timestamp + '</small>';
        historyHTML += '</div>';
        historyHTML += '<div class="row">';
        historyHTML += '<div class="col-md-4"><strong>Company Pair:</strong> ' + result.companyPair + '</div>';
        historyHTML += '<div class="col-md-4"><strong>Statement Period:</strong> ' + result.statementPeriod + '</div>';
        historyHTML += '<div class="col-md-4"><strong>Matches Found:</strong> ' + result.matchesFound + ' transactions</div>';
        historyHTML += '</div>';
        historyHTML += '</div>';
        historyHTML += '<div class="ms-3">';
        historyHTML += '<button type="button" class="btn btn-sm btn-outline-success me-2" onclick="viewReconciliationResults(\'' + result.companyPair + '\', \'' + result.statementPeriod + '\')">View Results</button>';
        historyHTML += '<button type="button" class="btn btn-sm btn-outline-danger" onclick="removeReconciliationFromHistory(' + (reconciliationHistory.length - 1 - index) + ')">Remove</button>';
        historyHTML += '</div>';
        historyHTML += '</div>';
        historyHTML += '</div>';
    });
    
    historyHTML += '<div class="mt-3">';
    historyHTML += '<button type="button" class="btn btn-sm btn-outline-secondary" onclick="clearAllReconciliationHistory()">';
    historyHTML += '<i class="bi bi-trash me-1"></i>Clear All History';
    historyHTML += '</button>';
    historyHTML += '</div>';
    historyHTML += '</div>';
    
    resultDiv.innerHTML = historyHTML;
}

// Function to remove a specific reconciliation from history
function removeReconciliationFromHistory(index) {
    if (index >= 0 && index < reconciliationHistory.length) {
        reconciliationHistory.splice(index, 1);
        displayReconciliationHistory();
    }
}

// Function to clear all reconciliation history
function clearAllReconciliationHistory() {
    reconciliationHistory = [];
    displayReconciliationHistory();
}

// Function to view reconciliation results with automatic company pair and period selection
function viewReconciliationResults(companyPair, statementPeriod) {
    // Navigate to matched results page
    showTab('matched-results');
    
    // Wait for the page to load and company pairs to be loaded
    setTimeout(() => {
        const companySelect = document.getElementById('matched-company-pair-select');
        const periodSelect = document.getElementById('matched-period-select');
        
        if (companySelect && companyPair && companyPair !== 'All Companies') {
            // Find and select the company pair
            for (let i = 0; i < companySelect.options.length; i++) {
                if (companySelect.options[i].text === companyPair) {
                    companySelect.selectedIndex = i;
                    break;
                }
            }
            
            // Trigger the change event to load periods for this company pair
            if (companySelect) {
                companySelect.dispatchEvent(new Event('change'));
                
                // Wait for periods to be loaded, then select the period
                setTimeout(() => {
                    if (periodSelect && statementPeriod && statementPeriod !== 'All Periods') {
                        // Find and select the statement period
                        for (let i = 0; i < periodSelect.options.length; i++) {
                            if (periodSelect.options[i].text === statementPeriod) {
                                periodSelect.selectedIndex = i;
                                periodSelect.dispatchEvent(new Event('change'));
                                break;
                            }
                        }
                        
                        // Load the matched results automatically
                        loadMatchesInViewer();
                    }
                }, 200); // Wait for periods to load
            }
        }
    }, 100);
}

// Function to clear the reconciliation notification (legacy function for backward compatibility)
function clearReconciliationNotification() {
    clearAllReconciliationHistory();
}

// Function to truncate the database table
async function truncateTable() {
    if (!confirm('⚠️ WARNING: This will permanently delete ALL data in the table!\n\nThis action cannot be undone. Are you sure you want to continue?')) {
        return;
    }
    
    const resultDiv = document.getElementById('truncate-result');
    resultDiv.innerHTML = '<div class="alert alert-warning"><i class="bi bi-exclamation-triangle me-2"></i>Truncating table...</div>';
    
    try {
        const response = await fetch('/api/truncate-table', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            }
        });
        
        const result = await response.json();
        
        if (response.ok && result.success) {
            resultDiv.innerHTML = `<div class="alert alert-success"><i class="bi bi-check-circle me-2"></i>${result.message}</div>`;
            
            // Refresh data displays
            setTimeout(() => {
                loadData();
                loadUnreconciledPairs();
                showNotification('Table truncated successfully. All data has been cleared.', 'success');
            }, 1000);
        } else {
            resultDiv.innerHTML = `<div class="alert alert-danger"><i class="bi bi-exclamation-circle me-2"></i>Failed to truncate table: ${result.error || 'Unknown error'}</div>`;
        }
    } catch (error) {
        resultDiv.innerHTML = `<div class="alert alert-danger"><i class="bi bi-exclamation-circle me-2"></i>Error: ${error.message}</div>`;
    }
}

// Function to reset all matches
async function resetAllMatches() {
    if (!confirm('⚠️ WARNING: This will reset all match status columns!\n\nThis will make all transactions available for matching again. Are you sure you want to continue?')) {
        return;
    }
    
    const resultDiv = document.getElementById('reset-matches-result');
    resultDiv.innerHTML = '<div class="alert alert-warning"><i class="bi bi-exclamation-triangle me-2"></i>Resetting all matches...</div>';
    
    try {
        const response = await fetch('/api/reset-all-matches', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            }
        });
        
        const result = await response.json();
        
        if (response.ok && result.success) {
            resultDiv.innerHTML = `<div class="alert alert-success"><i class="bi bi-check-circle me-2"></i>${result.message}</div>`;
            
            // Refresh data displays
            setTimeout(() => {
                loadData();
                loadUnreconciledPairs();
                showNotification('All matches reset successfully. Transactions are now available for matching again.', 'success');
            }, 1000);
        } else {
            resultDiv.innerHTML = `<div class="alert alert-danger"><i class="bi bi-exclamation-circle me-2"></i>Failed to reset matches: ${result.error || 'Unknown error'}</div>`;
        }
    } catch (error) {
        resultDiv.innerHTML = `<div class="alert alert-danger"><i class="bi bi-exclamation-circle me-2"></i>Error: ${error.message}</div>`;
    }
}

async function downloadAutoMatches() {
    try {
        // Get selected company pair and period
        const companySelect = document.getElementById('matched-company-pair-select');
        const periodSelect = document.getElementById('matched-period-select');
        const companyPair = companySelect ? companySelect.value : '';
        const period = periodSelect ? periodSelect.value : '';
        
        let lenderCompany = '';
        let borrowerCompany = '';
        let month = '';
        let year = '';
        
        if (companyPair && companyPair.includes('↔')) {
            const parts = companyPair.split('↔').map(s => s.trim());
            lenderCompany = parts[0];
            borrowerCompany = parts[1];
        }
        
        if (period && period !== '-- All Periods --') {
            const periodParts = period.split(' ');
            if (periodParts.length === 2) {
                month = periodParts[0];
                year = periodParts[1];
            }
        }
        
        // Build query string
        let url = '/api/download-matches';
        const params = [];
        if (lenderCompany && borrowerCompany) {
            params.push(`lender_company=${encodeURIComponent(lenderCompany)}`);
            params.push(`borrower_company=${encodeURIComponent(borrowerCompany)}`);
        }
        if (month) params.push(`month=${encodeURIComponent(month)}`);
        if (year) params.push(`year=${encodeURIComponent(year)}`);
        if (params.length > 0) {
            url += '?' + params.join('&');
        }
        
        // Show loading state
        const downloadBtn = document.getElementById('download-matched-btn');
        const originalText = downloadBtn.innerHTML;
        downloadBtn.innerHTML = '<i class="bi bi-hourglass-split me-2"></i>Downloading...';
        downloadBtn.disabled = true;
        
        // Trigger download
        window.location.href = url;
        
        // Reset button after a delay
        setTimeout(() => {
            downloadBtn.innerHTML = originalText;
            downloadBtn.disabled = false;
        }, 2000);
        
    } catch (error) {
        console.error('Error downloading auto-matched results:', error);
        showNotification('Failed to download auto-matched results', 'error');
        
        // Reset button
        const downloadBtn = document.getElementById('download-matched-btn');
        downloadBtn.innerHTML = '<i class="bi bi-download me-2"></i>Download Auto-Matched Results';
        downloadBtn.disabled = false;
    }
}