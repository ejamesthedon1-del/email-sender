"""
Email Outreach System - Automated email outreach with SMTP rotation and follow-ups
"""

__version__ = "1.0.0"

from .smtp_manager import SMTPAccount, SMTPManager
from .template_engine import TemplateProcessor
from .contact_manager import Contact, ContactManager
from .email_sender import EmailSender, SendResult
from .scheduler import FollowUpScheduler, FollowUpRule, FollowUpTrigger
from .utils import load_smtp_accounts_from_env, setup_logging

__all__ = [
    'SMTPAccount',
    'SMTPManager',
    'TemplateProcessor',
    'Contact',
    'ContactManager',
    'EmailSender',
    'SendResult',
    'FollowUpScheduler',
    'FollowUpRule',
    'FollowUpTrigger',
    'load_smtp_accounts_from_env',
    'setup_logging',
]

