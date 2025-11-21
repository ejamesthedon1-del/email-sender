"""
Dashboard API endpoints
"""
from flask import Blueprint, jsonify
from app.models import Storage
from src import SMTPManager, SMTPAccount
from src.utils import load_smtp_accounts_from_env
from datetime import datetime

bp = Blueprint('dashboard', __name__, url_prefix='/api/dashboard')

@bp.route('/stats', methods=['GET'])
def get_stats():
    """Get dashboard statistics"""
    # Load campaigns
    campaigns = Storage.load('campaigns')
    
    # Load contacts
    contacts = Storage.load('contacts')
    
    # Load SMTP accounts
    smtp_accounts = Storage.load('smtp_accounts')
    
    # Calculate statistics
    total_campaigns = len(campaigns)
    active_campaigns = len([c for c in campaigns if c.get('status') == 'running'])
    total_contacts = len(contacts)
    pending_contacts = len([c for c in contacts if c.get('status') == 'pending'])
    sent_contacts = len([c for c in contacts if c.get('status') == 'sent'])
    
    # Calculate total emails sent
    total_sent = sum(c.get('emails_sent', 0) for c in campaigns)
    total_failed = sum(c.get('emails_failed', 0) for c in campaigns)
    
    # Get SMTP account stats
    try:
        accounts = load_smtp_accounts_from_env()
        if not accounts and smtp_accounts:
            # Try to create accounts from storage
            accounts = []
            for acc_data in smtp_accounts:
                try:
                    acc = SMTPAccount(
                        name=acc_data.get('name', ''),
                        host=acc_data.get('host', ''),
                        port=acc_data.get('port', 587),
                        username=acc_data.get('username', ''),
                        password=acc_data.get('password', ''),
                        from_email=acc_data.get('from_email', ''),
                        from_name=acc_data.get('from_name', ''),
                        use_tls=acc_data.get('use_tls', True),
                        use_ssl=acc_data.get('use_ssl', False),
                        daily_limit=acc_data.get('daily_limit', 500),
                        hourly_limit=acc_data.get('hourly_limit', 50),
                        delay_between_emails=acc_data.get('delay_between_emails', 2.0)
                    )
                    accounts.append(acc)
                except:
                    pass
        
        if accounts:
            smtp_manager = SMTPManager(accounts)
            account_stats = smtp_manager.get_account_stats()
        else:
            account_stats = {}
    except:
        account_stats = {}
    
    return jsonify({
        'campaigns': {
            'total': total_campaigns,
            'active': active_campaigns,
            'completed': len([c for c in campaigns if c.get('status') == 'completed'])
        },
        'contacts': {
            'total': total_contacts,
            'pending': pending_contacts,
            'sent': sent_contacts,
            'failed': len([c for c in contacts if c.get('status') == 'failed'])
        },
        'emails': {
            'total_sent': total_sent,
            'total_failed': total_failed,
            'success_rate': (total_sent / (total_sent + total_failed) * 100) if (total_sent + total_failed) > 0 else 0
        },
        'smtp_accounts': {
            'total': len(smtp_accounts),
            'active': len([a for a in smtp_accounts if a.get('is_active', True)]),
            'stats': account_stats
        }
    })

@bp.route('/recent-campaigns', methods=['GET'])
def get_recent_campaigns():
    """Get recent campaigns"""
    campaigns = Storage.load('campaigns')
    # Sort by created_at, most recent first
    campaigns.sort(key=lambda x: x.get('created_at', ''), reverse=True)
    return jsonify(campaigns[:10])  # Return last 10

