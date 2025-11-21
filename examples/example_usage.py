#!/usr/bin/env python3
"""
Example usage of the Email Outreach System
"""
from src import (
    SMTPAccount, SMTPManager,
    TemplateProcessor,
    ContactManager, Contact,
    EmailSender,
    FollowUpScheduler, FollowUpRule, FollowUpTrigger
)
from src.utils import setup_logging
from datetime import datetime, timedelta

# Setup logging
setup_logging("INFO")

# Create SMTP accounts
accounts = [
    SMTPAccount(
        name="Gmail_Account_1",
        host="smtp.gmail.com",
        port=587,
        username="your_email@gmail.com",
        password="your_app_password",
        from_email="your_email@gmail.com",
        from_name="Your Name",
        use_tls=True,
        daily_limit=500,
        hourly_limit=50,
        delay_between_emails=2.0
    )
]

smtp_manager = SMTPManager(accounts)

# Create contacts
contact_manager = ContactManager()
contact_manager.add_contact(Contact(
    email="john.doe@example.com",
    first_name="John",
    last_name="Doe",
    brokerage="ABC Realty",
    city="New York",
    state="NY",
    custom1="Commercial",
    custom2="5 years"
))

contact_manager.add_contact(Contact(
    email="jane.smith@example.com",
    first_name="Jane",
    last_name="Smith",
    brokerage="XYZ Properties",
    city="Los Angeles",
    state="CA",
    custom1="Residential",
    custom2="10 years"
))

# Initialize template processor
template_processor = TemplateProcessor()

# Initialize email sender
email_sender = EmailSender(smtp_manager, template_processor)

# Define templates
subject_template = "Quick question about {Brokerage} in {City}"
body_template = """Hi {FirstName},

I hope this email finds you well. I noticed you're with {Brokerage} in {City}, and I wanted to reach out about a potential opportunity.

Based on your experience with {Custom1} properties and your {Custom2} in the industry, I thought you might be interested.

Would you be open to a quick 15-minute conversation this week?

Best regards,
Your Name"""

# Send campaign
print("Sending campaign...")
contacts = contact_manager.get_pending_contacts()

def progress_callback(current, total, result):
    status = "✓" if result.success else "✗"
    print(f"[{current}/{total}] {status} {result.contact_email}")

stats = email_sender.send_campaign(
    contacts=contacts,
    subject_template=subject_template,
    body_template=body_template,
    progress_callback=progress_callback
)

print(f"\nCampaign completed:")
print(f"  Total: {stats['total']}")
print(f"  Successful: {stats['successful']}")
print(f"  Failed: {stats['failed']}")
print(f"  Success Rate: {stats['success_rate']:.2f}%")

# Setup follow-up rule
scheduler = FollowUpScheduler(contact_manager, email_sender)

followup_rule = FollowUpRule(
    name="First Follow-up",
    trigger=FollowUpTrigger.DAYS_AFTER_NO_REPLY,
    days=3,
    subject_template="Re: Quick question about {Brokerage}",
    body_template="Hi {FirstName},\n\nI wanted to follow up on my previous email. I know you're busy, but I'd love to connect if you have a moment.\n\nBest regards,\nYour Name",
    max_followups=1,
    enabled=True
)

scheduler.add_rule(followup_rule)

# Process follow-ups (in a real scenario, you'd run this later)
print("\nFollow-up rule added. Run scheduler.process_followups() after 3 days to send follow-ups.")

# Clean up
smtp_manager.close_all_connections()

print("\nDone!")

