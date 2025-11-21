"""
Campaign API endpoints
"""
import threading
from flask import Blueprint, jsonify, request
from app.models import Storage
from src import SMTPManager, SMTPAccount, TemplateProcessor, ContactManager, EmailSender
from src.utils import load_smtp_accounts_from_env, setup_logging
import logging

bp = Blueprint('campaigns', __name__, url_prefix='/api/campaigns')
logger = logging.getLogger(__name__)

# Store active campaign threads
active_campaigns = {}

def run_campaign(campaign_id: str, campaign_data: dict):
    """Run a campaign in a background thread"""
    try:
        # Update campaign status
        from datetime import datetime
        Storage.update('campaigns', campaign_id, {'status': 'running', 'started_at': datetime.now().isoformat()})
        
        # Load SMTP accounts
        smtp_accounts_data = Storage.load('smtp_accounts')
        accounts = []
        for acc_data in smtp_accounts_data:
            if acc_data.get('is_active', True):
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
                except Exception as e:
                    logger.error(f"Error creating SMTP account {acc_data.get('name')}: {str(e)}")
        
        if not accounts:
            Storage.update('campaigns', campaign_id, {
                'status': 'failed',
                'error': 'No active SMTP accounts available'
            })
            return
        
        smtp_manager = SMTPManager(accounts)
        template_processor = TemplateProcessor()
        email_sender = EmailSender(smtp_manager, template_processor)
        
        # Load contacts
        contact_manager = ContactManager()
        contacts_data = Storage.load('contacts')
        
        # Filter contacts based on campaign settings
        contact_ids = campaign_data.get('contact_ids', [])
        if contact_ids:
            contacts_data = [c for c in contacts_data if str(c.get('id')) in [str(cid) for cid in contact_ids]]
        
        # Convert to Contact objects
        from src.contact_manager import Contact
        from datetime import datetime
        
        contacts = []
        for c_data in contacts_data:
            if c_data.get('status') == 'pending' or campaign_data.get('resend', False):
                contact = Contact(
                    email=c_data.get('email', ''),
                    first_name=c_data.get('first_name', ''),
                    last_name=c_data.get('last_name', ''),
                    company=c_data.get('company', ''),
                    brokerage=c_data.get('brokerage', ''),
                    city=c_data.get('city', ''),
                    state=c_data.get('state', ''),
                    custom1=c_data.get('custom1', ''),
                    custom2=c_data.get('custom2', ''),
                    custom3=c_data.get('custom3', ''),
                    custom4=c_data.get('custom4', ''),
                    custom5=c_data.get('custom5', ''),
                    status=c_data.get('status', 'pending')
                )
                contacts.append(contact)
        
        if not contacts:
            Storage.update('campaigns', campaign_id, {
                'status': 'completed',
                'emails_sent': 0,
                'emails_failed': 0,
                'error': 'No contacts to send to'
            })
            return
        
        # Get templates
        template_id = campaign_data.get('template_id')
        templates_data = Storage.load('templates')
        template = next((t for t in templates_data if str(t.get('id')) == str(template_id)), None)
        
        if not template:
            Storage.update('campaigns', campaign_id, {
                'status': 'failed',
                'error': 'Template not found'
            })
            return
        
        subject_template = template.get('subject', '')
        body_template = template.get('body', '')
        html_template = template.get('html_body')
        
        # Send campaign
        max_emails = campaign_data.get('max_emails')
        
        def progress_callback(current, total, result):
            # Update campaign progress
            Storage.update('campaigns', campaign_id, {
                'progress': {
                    'current': current,
                    'total': total,
                    'percentage': (current / total * 100) if total > 0 else 0
                },
                'last_sent': result.contact_email,
                'last_status': 'success' if result.success else 'failed'
            })
            
            # Update contact status
            contacts_storage = Storage.load('contacts')
            for c in contacts_storage:
                if c.get('email') == result.contact_email:
                    if result.success:
                        c['status'] = 'sent'
                        c['sent_count'] = c.get('sent_count', 0) + 1
                        c['last_sent_date'] = datetime.now().isoformat()
                    else:
                        c['status'] = 'failed'
                    Storage.save('contacts', contacts_storage)
                    break
        
        stats = email_sender.send_campaign(
            contacts=contacts,
            subject_template=subject_template,
            body_template=body_template,
            html_template=html_template,
            max_emails=max_emails,
            progress_callback=progress_callback
        )
        
        # Update campaign with results
        Storage.update('campaigns', campaign_id, {
            'status': 'completed',
            'emails_sent': stats['successful'],
            'emails_failed': stats['failed'],
            'completed_at': datetime.now().isoformat()
        })
        
        smtp_manager.close_all_connections()
        
    except Exception as e:
        logger.error(f"Error running campaign {campaign_id}: {str(e)}")
        Storage.update('campaigns', campaign_id, {
            'status': 'failed',
            'error': str(e)
        })
    finally:
        if campaign_id in active_campaigns:
            del active_campaigns[campaign_id]

@bp.route('', methods=['GET'])
def get_campaigns():
    """Get all campaigns"""
    campaigns = Storage.load('campaigns')
    return jsonify(campaigns)

@bp.route('/<campaign_id>', methods=['GET'])
def get_campaign(campaign_id):
    """Get a specific campaign"""
    campaign = Storage.get('campaigns', campaign_id)
    if not campaign:
        return jsonify({'error': 'Campaign not found'}), 404
    return jsonify(campaign)

@bp.route('', methods=['POST'])
def create_campaign():
    """Create a new campaign"""
    data = request.json
    
    campaign = {
        'name': data.get('name', 'Untitled Campaign'),
        'template_id': data.get('template_id'),
        'contact_ids': data.get('contact_ids', []),
        'max_emails': data.get('max_emails'),
        'resend': data.get('resend', False),
        'status': 'pending',
        'emails_sent': 0,
        'emails_failed': 0,
        'progress': {'current': 0, 'total': 0, 'percentage': 0}
    }
    
    campaign = Storage.add('campaigns', campaign)
    return jsonify(campaign), 201

@bp.route('/<campaign_id>/start', methods=['POST'])
def start_campaign(campaign_id):
    """Start a campaign"""
    campaign = Storage.get('campaigns', campaign_id)
    if not campaign:
        return jsonify({'error': 'Campaign not found'}), 404
    
    if campaign.get('status') == 'running':
        return jsonify({'error': 'Campaign is already running'}), 400
    
    # Start campaign in background thread
    thread = threading.Thread(target=run_campaign, args=(campaign_id, campaign))
    thread.daemon = True
    thread.start()
    
    active_campaigns[campaign_id] = thread
    
    return jsonify({'status': 'started'})

@bp.route('/<campaign_id>', methods=['PUT'])
def update_campaign(campaign_id):
    """Update a campaign"""
    data = request.json
    campaign = Storage.update('campaigns', campaign_id, data)
    if not campaign:
        return jsonify({'error': 'Campaign not found'}), 404
    return jsonify(campaign)

@bp.route('/<campaign_id>', methods=['DELETE'])
def delete_campaign(campaign_id):
    """Delete a campaign"""
    if Storage.delete('campaigns', campaign_id):
        return jsonify({'status': 'deleted'})
    return jsonify({'error': 'Campaign not found'}), 404

