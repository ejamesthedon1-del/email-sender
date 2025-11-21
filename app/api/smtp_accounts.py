"""
SMTP Accounts API endpoints
"""
from flask import Blueprint, jsonify, request
from app.models import Storage

bp = Blueprint('smtp_accounts', __name__, url_prefix='/api/smtp-accounts')

@bp.route('', methods=['GET'])
def get_accounts():
    """Get all SMTP accounts"""
    accounts = Storage.load('smtp_accounts')
    # Don't return passwords in the list
    for account in accounts:
        if 'password' in account:
            account['password'] = '***hidden***'
    return jsonify(accounts)

@bp.route('/<account_id>', methods=['GET'])
def get_account(account_id):
    """Get a specific SMTP account"""
    account = Storage.get('smtp_accounts', account_id)
    if not account:
        return jsonify({'error': 'Account not found'}), 404
    # Don't return password
    if 'password' in account:
        account['password'] = '***hidden***'
    return jsonify(account)

@bp.route('', methods=['POST'])
def create_account():
    """Create a new SMTP account"""
    data = request.json
    
    account = {
        'name': data.get('name', ''),
        'host': data.get('host', ''),
        'port': data.get('port', 587),
        'username': data.get('username', ''),
        'password': data.get('password', ''),
        'from_email': data.get('from_email', ''),
        'from_name': data.get('from_name', ''),
        'use_tls': data.get('use_tls', True),
        'use_ssl': data.get('use_ssl', False),
        'daily_limit': data.get('daily_limit', 500),
        'hourly_limit': data.get('hourly_limit', 50),
        'delay_between_emails': data.get('delay_between_emails', 2.0),
        'is_active': data.get('is_active', True)
    }
    
    account = Storage.add('smtp_accounts', account)
    # Don't return password
    account['password'] = '***hidden***'
    return jsonify(account), 201

@bp.route('/<account_id>', methods=['PUT'])
def update_account(account_id):
    """Update an SMTP account"""
    data = request.json
    # If password is being updated with hidden value, don't update it
    if data.get('password') == '***hidden***':
        data.pop('password')
    account = Storage.update('smtp_accounts', account_id, data)
    if not account:
        return jsonify({'error': 'Account not found'}), 404
    # Don't return password
    account['password'] = '***hidden***'
    return jsonify(account)

@bp.route('/<account_id>', methods=['DELETE'])
def delete_account(account_id):
    """Delete an SMTP account"""
    if Storage.delete('smtp_accounts', account_id):
        return jsonify({'status': 'deleted'})
    return jsonify({'error': 'Account not found'}), 404

@bp.route('/<account_id>/test', methods=['POST'])
def test_account(account_id):
    """Test SMTP account connection"""
    account_data = Storage.get('smtp_accounts', account_id)
    if not account_data:
        return jsonify({'error': 'Account not found'}), 404
    
    try:
        from src import SMTPAccount, SMTPManager
        
        account = SMTPAccount(
            name=account_data.get('name', ''),
            host=account_data.get('host', ''),
            port=account_data.get('port', 587),
            username=account_data.get('username', ''),
            password=account_data.get('password', ''),
            from_email=account_data.get('from_email', ''),
            from_name=account_data.get('from_name', ''),
            use_tls=account_data.get('use_tls', True),
            use_ssl=account_data.get('use_ssl', False)
        )
        
        smtp_manager = SMTPManager([account])
        connection = smtp_manager.get_connection(account)
        
        if connection:
            smtp_manager.close_all_connections()
            return jsonify({'status': 'success', 'message': 'Connection successful'})
        else:
            return jsonify({'status': 'error', 'message': 'Connection failed'}), 400
            
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 400

