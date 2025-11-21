"""
Email Sender - Handles sending emails with batching, throttling, and error handling
"""
import logging
import time
from typing import List, Dict, Any, Optional, Callable
from datetime import datetime
from dataclasses import dataclass

from ..smtp_manager import SMTPManager, SMTPAccount
from ..contact_manager import Contact
from ..template_engine import TemplateProcessor

logger = logging.getLogger(__name__)


@dataclass
class SendResult:
    """Result of sending an email"""
    success: bool
    contact_email: str
    account_name: str
    error_message: Optional[str] = None
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()


class EmailSender:
    """Handles sending emails with batching, throttling, and error handling"""
    
    def __init__(self, smtp_manager: SMTPManager, template_processor: TemplateProcessor):
        self.smtp_manager = smtp_manager
        self.template_processor = template_processor
        self.results: List[SendResult] = []
        self.batch_size = 10
        self.batch_delay = 60  # Seconds between batches
        self.global_delay = 2.0  # Seconds between individual emails
    
    def send_to_contact(self, contact: Contact, subject_template: str, 
                       body_template: str, html_template: Optional[str] = None) -> SendResult:
        """
        Send an email to a single contact
        
        Args:
            contact: Contact to send email to
            subject_template: Email subject template with variables
            body_template: Email body template (plain text) with variables
            html_template: Optional HTML email body template
        
        Returns:
            SendResult object
        """
        # Get available SMTP account
        account = self.smtp_manager.get_available_account()
        if not account:
            return SendResult(
                success=False,
                contact_email=contact.email,
                account_name="none",
                error_message="No available SMTP accounts"
            )
        
        # Render templates with contact variables
        try:
            variables = contact.get_template_variables()
            subject = self.template_processor.get_rendered_subject(subject_template, variables)
            # Only render body if template is provided and not empty
            body = ""
            if body_template and body_template.strip():
                body = self.template_processor.get_rendered_body(body_template, variables)
            html_body = None
            if html_template and html_template.strip():
                html_body = self.template_processor.get_rendered_html(html_template, variables)
        except Exception as e:
            logger.error(f"Template rendering error for {contact.email}: {str(e)}")
            return SendResult(
                success=False,
                contact_email=contact.email,
                account_name=account.name,
                error_message=f"Template rendering error: {str(e)}"
            )
        
        # Send email
        success = self.smtp_manager.send_email(
            account=account,
            to_email=contact.email,
            subject=subject,
            body=body,
            html_body=html_body
        )
        
        result = SendResult(
            success=success,
            contact_email=contact.email,
            account_name=account.name,
            error_message=None if success else "SMTP send failed"
        )
        
        self.results.append(result)
        return result
    
    def send_batch(self, contacts: List[Contact], subject_template: str,
                   body_template: str, html_template: Optional[str] = None,
                   progress_callback: Optional[Callable[[int, int, SendResult], None]] = None) -> List[SendResult]:
        """
        Send emails to a batch of contacts with throttling
        
        Args:
            contacts: List of contacts to send emails to
            subject_template: Email subject template
            body_template: Email body template
            html_template: Optional HTML template
            progress_callback: Optional callback function(contact_index, total, result)
        
        Returns:
            List of SendResult objects
        """
        results = []
        total = len(contacts)
        
        logger.info(f"Starting batch send to {total} contacts")
        
        for i, contact in enumerate(contacts, 1):
            # Check if contact should receive email
            if contact.status == 'unsubscribed':
                logger.debug(f"Skipping unsubscribed contact: {contact.email}")
                continue
            
            # Send email
            result = self.send_to_contact(contact, subject_template, body_template, html_template)
            results.append(result)
            
            # Update contact status
            if result.success:
                contact.status = 'sent'
                contact.sent_count += 1
                contact.last_sent_date = datetime.now()
            else:
                contact.status = 'failed'
                if contact.notes:
                    contact.notes += f" | Error: {result.error_message}"
                else:
                    contact.notes = f"Error: {result.error_message}"
            
            # Progress callback
            if progress_callback:
                progress_callback(i, total, result)
            
            # Throttling delay (except for last email)
            if i < total:
                time.sleep(self.global_delay)
            
            # Batch delay
            if i % self.batch_size == 0 and i < total:
                logger.info(f"Batch of {self.batch_size} completed. Waiting {self.batch_delay}s before next batch...")
                time.sleep(self.batch_delay)
        
        logger.info(f"Batch send completed. Success: {sum(1 for r in results if r.success)}, Failed: {sum(1 for r in results if not r.success)}")
        return results
    
    def send_campaign(self, contacts: List[Contact], subject_template: str,
                     body_template: str, html_template: Optional[str] = None,
                     max_emails: Optional[int] = None,
                     progress_callback: Optional[Callable[[int, int, SendResult], None]] = None) -> Dict[str, Any]:
        """
        Send a full campaign to multiple contacts
        
        Args:
            contacts: List of contacts
            subject_template: Email subject template
            body_template: Email body template
            html_template: Optional HTML template
            max_emails: Maximum number of emails to send (None for all)
            progress_callback: Optional progress callback
        
        Returns:
            Campaign statistics dictionary
        """
        if max_emails:
            contacts = contacts[:max_emails]
        
        results = self.send_batch(contacts, subject_template, body_template, 
                                 html_template, progress_callback)
        
        # Calculate statistics
        total = len(results)
        successful = sum(1 for r in results if r.success)
        failed = total - successful
        
        stats = {
            'total': total,
            'successful': successful,
            'failed': failed,
            'success_rate': (successful / total * 100) if total > 0 else 0,
            'results': results
        }
        
        return stats
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get sending statistics"""
        if not self.results:
            return {'total': 0, 'successful': 0, 'failed': 0}
        
        total = len(self.results)
        successful = sum(1 for r in self.results if r.success)
        failed = total - successful
        
        # Group by account
        by_account = {}
        for result in self.results:
            if result.account_name not in by_account:
                by_account[result.account_name] = {'total': 0, 'successful': 0, 'failed': 0}
            by_account[result.account_name]['total'] += 1
            if result.success:
                by_account[result.account_name]['successful'] += 1
            else:
                by_account[result.account_name]['failed'] += 1
        
        return {
            'total': total,
            'successful': successful,
            'failed': failed,
            'success_rate': (successful / total * 100) if total > 0 else 0,
            'by_account': by_account
        }
    
    def clear_results(self):
        """Clear sending results"""
        self.results = []

