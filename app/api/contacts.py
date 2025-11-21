"""
Contacts API endpoints
"""
import csv
import io
from flask import Blueprint, jsonify, request
from app.models import Storage
from src.contact_manager import ContactManager, Contact

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

