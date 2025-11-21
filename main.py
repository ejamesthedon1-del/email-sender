#!/usr/bin/env python3
"""
Main entry point for the Email Outreach System
"""
import argparse
import sys
import json
from pathlib import Path
from datetime import datetime, timedelta

from src.smtp_manager import SMTPManager, SMTPAccount
from src.template_engine import TemplateProcessor
from src.contact_manager import ContactManager
from src.email_sender import EmailSender
from src.scheduler import FollowUpScheduler, FollowUpRule, FollowUpTrigger
from src.utils import load_smtp_accounts_from_env, setup_logging


def load_template_file(file_path: str) -> str:
    """Load template from file"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        print(f"Error loading template file {file_path}: {str(e)}")
        sys.exit(1)


def send_campaign(args):
    """Send a campaign to contacts"""
    # Setup logging
    setup_logging(args.log_level, args.log_file)
    
    # Load SMTP accounts
    if args.config_file:
        # Load from JSON config file
        with open(args.config_file, 'r') as f:
            config = json.load(f)
        accounts = [
            SMTPAccount(**acc_config) for acc_config in config.get('smtp_accounts', [])
        ]
    else:
        # Load from environment variables
        accounts = load_smtp_accounts_from_env()
    
    if not accounts:
        print("Error: No SMTP accounts configured. Please set up SMTP accounts in .env or config file.")
        sys.exit(1)
    
    smtp_manager = SMTPManager(accounts)
    
    # Load contacts
    contact_manager = ContactManager()
    contact_manager.load_from_csv(args.contacts_file)
    
    # Load templates
    subject_template = load_template_file(args.subject_template)
    body_template = load_template_file(args.body_template)
    html_template = None
    if args.html_template:
        html_template = load_template_file(args.html_template)
    
    # Initialize components
    template_processor = TemplateProcessor()
    email_sender = EmailSender(smtp_manager, template_processor)
    
    # Get contacts to send to
    if args.status:
        contacts = [c for c in contact_manager.contacts if c.status == args.status]
    else:
        contacts = contact_manager.get_pending_contacts()
    
    if not contacts:
        print("No contacts found to send emails to.")
        sys.exit(0)
    
    # Limit number of emails if specified
    if args.max_emails:
        contacts = contacts[:args.max_emails]
    
    print(f"Sending campaign to {len(contacts)} contacts...")
    
    # Progress callback
    def progress_callback(current, total, result):
        status = "✓" if result.success else "✗"
        print(f"[{current}/{total}] {status} {result.contact_email}")
    
    # Send campaign
    stats = email_sender.send_campaign(
        contacts=contacts,
        subject_template=subject_template,
        body_template=body_template,
        html_template=html_template,
        progress_callback=progress_callback
    )
    
    # Save updated contacts
    if args.output_file:
        contact_manager.save_to_csv(args.output_file)
    else:
        contact_manager.save_to_csv(args.contacts_file)
    
    # Print statistics
    print("\n" + "="*50)
    print("Campaign Statistics:")
    print(f"Total: {stats['total']}")
    print(f"Successful: {stats['successful']}")
    print(f"Failed: {stats['failed']}")
    print(f"Success Rate: {stats['success_rate']:.2f}%")
    print("="*50)
    
    # Close connections
    smtp_manager.close_all_connections()


def process_followups(args):
    """Process follow-up emails"""
    # Setup logging
    setup_logging(args.log_level, args.log_file)
    
    # Load SMTP accounts
    if args.config_file:
        with open(args.config_file, 'r') as f:
            config = json.load(f)
        accounts = [
            SMTPAccount(**acc_config) for acc_config in config.get('smtp_accounts', [])
        ]
    else:
        accounts = load_smtp_accounts_from_env()
    
    if not accounts:
        print("Error: No SMTP accounts configured.")
        sys.exit(1)
    
    smtp_manager = SMTPManager(accounts)
    
    # Load contacts
    contact_manager = ContactManager()
    contact_manager.load_from_csv(args.contacts_file)
    
    # Load follow-up rules
    with open(args.rules_file, 'r') as f:
        rules_config = json.load(f)
    
    # Initialize components
    template_processor = TemplateProcessor()
    email_sender = EmailSender(smtp_manager, template_processor)
    scheduler = FollowUpScheduler(contact_manager, email_sender)
    
    # Add follow-up rules
    for rule_config in rules_config.get('rules', []):
        rule = FollowUpRule(
            name=rule_config['name'],
            trigger=FollowUpTrigger(rule_config['trigger']),
            days=rule_config['days'],
            subject_template=rule_config['subject_template'],
            body_template=rule_config['body_template'],
            html_template=rule_config.get('html_template'),
            max_followups=rule_config.get('max_followups', 3),
            enabled=rule_config.get('enabled', True)
        )
        scheduler.add_rule(rule)
    
    print("Processing follow-ups...")
    
    # Process follow-ups
    stats = scheduler.process_followups()
    
    # Save updated contacts
    if args.output_file:
        contact_manager.save_to_csv(args.output_file)
    else:
        contact_manager.save_to_csv(args.contacts_file)
    
    # Print statistics
    print("\n" + "="*50)
    print("Follow-up Statistics:")
    print(f"Total: {stats['total']}")
    print(f"Successful: {stats['successful']}")
    print(f"Failed: {stats['failed']}")
    print(f"Success Rate: {stats['success_rate']:.2f}%")
    print("="*50)
    
    # Close connections
    smtp_manager.close_all_connections()


def main():
    parser = argparse.ArgumentParser(
        description='Automated Email Outreach System',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Send a campaign
  python main.py send --contacts contacts.csv --subject-template subject.txt --body-template body.txt
  
  # Process follow-ups
  python main.py followup --contacts contacts.csv --rules followup_rules.json
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Command to execute')
    
    # Send campaign command
    send_parser = subparsers.add_parser('send', help='Send a campaign')
    send_parser.add_argument('--contacts-file', required=True, help='CSV file with contacts')
    send_parser.add_argument('--subject-template', required=True, help='Subject template file')
    send_parser.add_argument('--body-template', required=True, help='Body template file')
    send_parser.add_argument('--html-template', help='HTML template file (optional)')
    send_parser.add_argument('--config-file', help='JSON config file with SMTP accounts')
    send_parser.add_argument('--max-emails', type=int, help='Maximum number of emails to send')
    send_parser.add_argument('--status', help='Filter contacts by status (default: pending)')
    send_parser.add_argument('--output-file', help='Output CSV file (default: overwrites input)')
    send_parser.add_argument('--log-level', default='INFO', help='Logging level (default: INFO)')
    send_parser.add_argument('--log-file', help='Log file path (optional)')
    
    # Follow-up command
    followup_parser = subparsers.add_parser('followup', help='Process follow-up emails')
    followup_parser.add_argument('--contacts-file', required=True, help='CSV file with contacts')
    followup_parser.add_argument('--rules-file', required=True, help='JSON file with follow-up rules')
    followup_parser.add_argument('--config-file', help='JSON config file with SMTP accounts')
    followup_parser.add_argument('--output-file', help='Output CSV file (default: overwrites input)')
    followup_parser.add_argument('--log-level', default='INFO', help='Logging level (default: INFO)')
    followup_parser.add_argument('--log-file', help='Log file path (optional)')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    try:
        if args.command == 'send':
            send_campaign(args)
        elif args.command == 'followup':
            process_followups(args)
    except KeyboardInterrupt:
        print("\nInterrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"Error: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
