"""
Contacts API endpoints
"""
import csv
import io
import os
import tempfile
import shutil
import logging
from flask import Blueprint, jsonify, request, send_from_directory, current_app
from werkzeug.utils import secure_filename
from app.models import Storage
from src.contact_manager import ContactManager, Contact

logger = logging.getLogger(__name__)

bp = Blueprint('contacts', __name__, url_prefix='/api/contacts')

@bp.route('', methods=['GET'])
def get_contacts():
    """Get all contacts"""
    contacts = Storage.load('contacts')
    return jsonify(contacts)

@bp.route('/<contact_id>', methods=['GET'])
def get_contact(contact_id):
    """Get a specific contact"""
    contact = Storage.get('contacts', contact_id)
    if not contact:
        return jsonify({'error': 'Contact not found'}), 404
    return jsonify(contact)

@bp.route('', methods=['POST'])
def create_contact():
    """Create a new contact"""
    data = request.json
    
    contact = {
        'email': data.get('email', ''),
        'first_name': data.get('first_name', ''),
        'last_name': data.get('last_name', ''),
        'company': data.get('company', ''),
        'brokerage': data.get('brokerage', ''),
        'city': data.get('city', ''),
        'state': data.get('state', ''),
        'custom1': data.get('custom1', ''),
        'custom2': data.get('custom2', ''),
        'custom3': data.get('custom3', ''),
        'custom4': data.get('custom4', ''),
        'custom5': data.get('custom5', ''),
        'status': data.get('status', 'pending'),
        'sent_count': data.get('sent_count', 0),
        'notes': data.get('notes', '')
    }
    
    contact = Storage.add('contacts', contact)
    return jsonify(contact), 201

@bp.route('/upload', methods=['POST'])
def upload_contacts():
    """Upload contacts from CSV file"""
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    try:
        # Read CSV file
        stream = io.StringIO(file.stream.read().decode("UTF8"), newline=None)
        csv_reader = csv.DictReader(stream)
        
        contacts_added = 0
        contacts_skipped = 0
        
        for row in csv_reader:
            # Normalize column names
            normalized_row = {k.lower().strip().replace(' ', '_'): v for k, v in row.items()}
            
            email = normalized_row.get('email', '').strip()
            if not email:
                contacts_skipped += 1
                continue
            
            # Check if contact already exists
            existing_contacts = Storage.load('contacts')
            if any(c.get('email', '').lower() == email.lower() for c in existing_contacts):
                contacts_skipped += 1
                continue
            
            contact = {
                'email': email,
                'first_name': normalized_row.get('first_name', '').strip(),
                'last_name': normalized_row.get('last_name', '').strip(),
                'company': normalized_row.get('company', '').strip(),
                'brokerage': normalized_row.get('brokerage', '').strip(),
                'city': normalized_row.get('city', '').strip(),
                'state': normalized_row.get('state', '').strip(),
                'custom1': normalized_row.get('custom1', '').strip(),
                'custom2': normalized_row.get('custom2', '').strip(),
                'custom3': normalized_row.get('custom3', '').strip(),
                'custom4': normalized_row.get('custom4', '').strip(),
                'custom5': normalized_row.get('custom5', '').strip(),
                'status': 'pending',
                'sent_count': 0
            }
            
            Storage.add('contacts', contact)
            contacts_added += 1
        
        return jsonify({
            'status': 'success',
            'contacts_added': contacts_added,
            'contacts_skipped': contacts_skipped
        })
        
    except Exception as e:
        return jsonify({'error': f'Error processing CSV: {str(e)}'}), 400

@bp.route('/<contact_id>', methods=['PUT'])
def update_contact(contact_id):
    """Update a contact"""
    data = request.json
    contact = Storage.update('contacts', contact_id, data)
    if not contact:
        return jsonify({'error': 'Contact not found'}), 404
    return jsonify(contact)

@bp.route('/<contact_id>', methods=['DELETE'])
def delete_contact(contact_id):
    """Delete a contact"""
    if Storage.delete('contacts', contact_id):
        return jsonify({'status': 'deleted'})
    return jsonify({'error': 'Contact not found'}), 404

@bp.route('/bulk-delete', methods=['POST'])
def bulk_delete_contacts():
    """Delete multiple contacts"""
    data = request.json
    contact_ids = data.get('contact_ids', [])
    
    deleted = 0
    for contact_id in contact_ids:
        if Storage.delete('contacts', contact_id):
            deleted += 1
    
    return jsonify({'status': 'success', 'deleted': deleted})

@bp.route('/validate-csv', methods=['POST'])
def validate_csv_emails():
    """Validate emails in a CSV file and return cleaned CSV"""
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    try:
        from src.utils.email_validator import validate_emails_in_csv, validate_single_email
        
        # Get optional email column name from request
        email_column = request.form.get('email_column', '').strip() or 'email'
        
        # Save uploaded file temporarily
        temp_dir = tempfile.gettempdir()
        input_path = os.path.join(temp_dir, secure_filename(file.filename))
        file.save(input_path)
        
        # First, detect the email column by reading the CSV
        detected_email_column = None
        invalid_emails_preview = []
        
        try:
            with open(input_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                fieldnames = reader.fieldnames
                if not fieldnames:
                    raise ValueError("CSV file has no headers")
                
                # Normalize column names for detection
                normalized_fieldnames = {name.lower().strip().replace(' ', '_'): name for name in fieldnames}
                
                # If user provided a column name, try to find it
                if email_column and email_column.lower() != 'email':
                    email_col_key = email_column.lower().strip().replace(' ', '_')
                    if email_col_key in normalized_fieldnames:
                        detected_email_column = normalized_fieldnames[email_col_key]
                    else:
                        # Try case-insensitive match
                        for key, original_name in normalized_fieldnames.items():
                            if key == email_col_key or original_name.lower() == email_column.lower():
                                detected_email_column = original_name
                                break
                else:
                    # Auto-detect: look for common email column names
                    for key, original_name in normalized_fieldnames.items():
                        if key == 'email' or 'email' in key:
                            detected_email_column = original_name
                            break
                
                if not detected_email_column:
                    # Fallback: use first column or 'email' if available
                    detected_email_column = fieldnames[0] if fieldnames else 'email'
                    logger.warning(f"Could not detect email column, using: {detected_email_column}")
                
                # Collect a preview of invalid emails for reporting
                f.seek(0)
                reader = csv.DictReader(f)
                for row_num, row in enumerate(reader, start=2):
                    email = row.get(detected_email_column, '').strip()
                    if email:
                        is_valid, error_msg = validate_single_email(email)
                        if not is_valid and len(invalid_emails_preview) < 10:
                            invalid_emails_preview.append({
                                'email': email,
                                'row': row_num,
                                'error': error_msg[:50]  # Truncate error message
                            })
        except Exception as e:
            logger.error(f"Error reading CSV for preview: {str(e)}")
            # Continue anyway - validation will catch the error
        
        # Use detected column for validation
        email_column_to_use = detected_email_column or email_column
        logger.info(f"Validating CSV file: {file.filename}")
        logger.info(f"Detected email column: {email_column_to_use}")
        logger.info(f"Total preview invalid emails collected: {len(invalid_emails_preview)}")
        
        # Validate emails and create cleaned CSV
        valid_count, invalid_count, validated_file = validate_emails_in_csv(
            input_file=input_path,
            output_file=os.path.join(temp_dir, f"{os.path.splitext(secure_filename(file.filename))[0]}_validated.csv"),
            email_column=email_column_to_use
        )
        
        logger.info(f"Validation results - Valid: {valid_count}, Invalid: {invalid_count}, Output: {validated_file}")
        
        if not validated_file or not os.path.exists(validated_file):
            # Clean up temp files
            try:
                if os.path.exists(input_path):
                    os.remove(input_path)
            except:
                pass
            
            return jsonify({
                'error': 'No valid emails found in CSV',
                'valid_count': valid_count,
                'invalid_count': invalid_count,
                'total_count': valid_count + invalid_count,
                'invalid_emails': invalid_emails_preview
            }), 400
        
        # Generate base name for download file
        base_name = os.path.splitext(secure_filename(file.filename))[0]
        
        # Save validated file to uploads directory for download
        uploads_dir = current_app.config.get('UPLOAD_FOLDER', 
            os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'uploads'))
        os.makedirs(uploads_dir, exist_ok=True)
        
        download_filename = f"{base_name}_validated.csv"
        download_path = os.path.join(uploads_dir, download_filename)
        
        # Copy validated file to uploads directory
        shutil.copy2(validated_file, download_path)
        
        # Clean up temp files
        try:
            if os.path.exists(input_path):
                os.remove(input_path)
            if os.path.exists(validated_file):
                os.remove(validated_file)
        except:
            pass
        
        # Read validated CSV content to return
        validated_csv_content = None
        try:
            with open(download_path, 'r', encoding='utf-8') as f:
                validated_csv_content = f.read()
        except Exception as e:
            logger.error(f"Error reading validated CSV: {str(e)}")
        
        # Convert invalid_emails_preview to a simple list of strings for frontend display
        invalid_emails_list = []
        for item in invalid_emails_preview:
            if isinstance(item, dict):
                invalid_emails_list.append(f"Row {item.get('row', '?')}: {item.get('email', '')} ({item.get('error', 'Invalid')[:50]})")
            else:
                invalid_emails_list.append(str(item))
        
        # Collect sample valid emails for verification (first 5)
        sample_valid_emails = []
        try:
            if validated_file and os.path.exists(validated_file):
                with open(validated_file, 'r', encoding='utf-8') as f:
                    reader = csv.DictReader(f)
                    for i, row in enumerate(reader):
                        if i >= 5:
                            break
                        email = row.get(email_column_to_use, '').strip()
                        if email:
                            sample_valid_emails.append(email)
        except Exception as e:
            logger.debug(f"Error collecting sample valid emails: {str(e)}")
        
        return jsonify({
            'status': 'success',
            'valid_count': valid_count,
            'invalid_count': invalid_count,
            'total_count': valid_count + invalid_count,
            'invalid_emails': invalid_emails_list,  # First 10 invalid emails with details
            'sample_valid_emails': sample_valid_emails[:5],  # First 5 valid emails for verification
            'email_column_used': email_column_to_use,
            'download_url': f'/api/contacts/download-validated/{download_filename}',
            'cleaned_csv_content': validated_csv_content,
            'output_filename': download_filename
        })
        
    except Exception as e:
        logger.error(f"Error validating CSV: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': f'Error validating CSV: {str(e)}'}), 400

@bp.route('/download-validated/<filename>', methods=['GET'])
def download_validated_csv(filename):
    """Download validated CSV file"""
    # Security: ensure filename is safe
    filename = secure_filename(filename)
    uploads_dir = current_app.config.get('UPLOAD_FOLDER', 
        os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'uploads'))
    
    if not os.path.exists(os.path.join(uploads_dir, filename)):
        return jsonify({'error': 'File not found'}), 404
    
    return send_from_directory(uploads_dir, filename, as_attachment=True)

