"""
Follow-up Scheduler - Handles automated follow-ups based on rules
"""
import logging
from typing import List, Dict, Any, Optional, Callable
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum

from ..contact_manager import Contact, ContactManager
from ..email_sender import EmailSender

logger = logging.getLogger(__name__)


class FollowUpTrigger(Enum):
    """Types of follow-up triggers"""
    DAYS_AFTER_SEND = "days_after_send"
    DAYS_AFTER_FAILURE = "days_after_failure"
    DAYS_AFTER_NO_REPLY = "days_after_no_reply"
    IMMEDIATE = "immediate"


@dataclass
class FollowUpRule:
    """Defines a follow-up rule"""
    name: str
    trigger: FollowUpTrigger
    days: int  # Number of days to wait
    subject_template: str
    body_template: str
    html_template: Optional[str] = None
    max_followups: int = 3  # Maximum number of times to follow up
    enabled: bool = True
    
    def should_trigger(self, contact: Contact, current_date: datetime = None) -> bool:
        """Check if this rule should trigger for a contact"""
        if not self.enabled:
            return False
        
        if current_date is None:
            current_date = datetime.now()
        
        if self.trigger == FollowUpTrigger.DAYS_AFTER_SEND:
            if not contact.last_sent_date:
                return False
            days_since = (current_date - contact.last_sent_date).days
            return days_since >= self.days
        
        elif self.trigger == FollowUpTrigger.DAYS_AFTER_FAILURE:
            if contact.status != 'failed':
                return False
            if not contact.last_sent_date:
                return False
            days_since = (current_date - contact.last_sent_date).days
            return days_since >= self.days
        
        elif self.trigger == FollowUpTrigger.DAYS_AFTER_NO_REPLY:
            if contact.status != 'sent':
                return False
            if not contact.last_sent_date:
                return False
            days_since = (current_date - contact.last_sent_date).days
            return days_since >= self.days
        
        elif self.trigger == FollowUpTrigger.IMMEDIATE:
            return True
        
        return False


class FollowUpScheduler:
    """Manages automated follow-ups"""
    
    def __init__(self, contact_manager: ContactManager, email_sender: EmailSender):
        self.contact_manager = contact_manager
        self.email_sender = email_sender
        self.rules: List[FollowUpRule] = []
        self.followup_history: Dict[str, List[Dict[str, Any]]] = {}  # email -> list of followups
    
    def add_rule(self, rule: FollowUpRule):
        """Add a follow-up rule"""
        self.rules.append(rule)
        logger.info(f"Added follow-up rule: {rule.name}")
    
    def remove_rule(self, rule_name: str):
        """Remove a follow-up rule"""
        self.rules = [r for r in self.rules if r.name != rule_name]
        logger.info(f"Removed follow-up rule: {rule_name}")
    
    def get_contacts_for_followup(self, current_date: Optional[datetime] = None) -> List[tuple[Contact, FollowUpRule]]:
        """
        Get contacts that need follow-ups based on rules
        
        Returns:
            List of (contact, rule) tuples
        """
        if current_date is None:
            current_date = datetime.now()
        
        contacts_to_followup = []
        
        for contact in self.contact_manager.contacts:
            if contact.status == 'unsubscribed':
                continue
            
            # Check each rule
            for rule in self.rules:
                if not rule.enabled:
                    continue
                
                # Check if we've exceeded max followups for this rule
                followup_count = self.get_followup_count(contact.email, rule.name)
                if followup_count >= rule.max_followups:
                    continue
                
                # Check if rule should trigger
                if rule.should_trigger(contact, current_date):
                    contacts_to_followup.append((contact, rule))
                    break  # Only one follow-up per contact at a time
        
        return contacts_to_followup
    
    def process_followups(self, progress_callback: Optional[Callable[[int, int, Dict], None]] = None) -> Dict[str, Any]:
        """
        Process all pending follow-ups
        
        Returns:
            Statistics about follow-ups processed
        """
        contacts_to_followup = self.get_contacts_for_followup()
        
        if not contacts_to_followup:
            logger.info("No contacts need follow-ups at this time")
            return {'total': 0, 'successful': 0, 'failed': 0}
        
        logger.info(f"Processing {len(contacts_to_followup)} follow-ups")
        
        results = []
        total = len(contacts_to_followup)
        
        for i, (contact, rule) in enumerate(contacts_to_followup, 1):
            # Send follow-up email
            result = self.email_sender.send_to_contact(
                contact=contact,
                subject_template=rule.subject_template,
                body_template=rule.body_template,
                html_template=rule.html_template
            )
            
            # Record follow-up
            if contact.email not in self.followup_history:
                self.followup_history[contact.email] = []
            
            self.followup_history[contact.email].append({
                'rule_name': rule.name,
                'timestamp': datetime.now().isoformat(),
                'success': result.success,
                'error': result.error_message
            })
            
            # Update contact
            if result.success:
                contact.last_sent_date = datetime.now()
                contact.sent_count += 1
                # Schedule next follow-up if needed
                followup_count = self.get_followup_count(contact.email, rule.name)
                if followup_count < rule.max_followups:
                    contact.follow_up_date = datetime.now() + timedelta(days=rule.days)
            else:
                contact.status = 'failed'
            
            results.append({
                'contact_email': contact.email,
                'rule_name': rule.name,
                'success': result.success
            })
            
            if progress_callback:
                progress_callback(i, total, results[-1])
        
        successful = sum(1 for r in results if r['success'])
        failed = len(results) - successful
        
        stats = {
            'total': total,
            'successful': successful,
            'failed': failed,
            'success_rate': (successful / total * 100) if total > 0 else 0
        }
        
        logger.info(f"Follow-ups processed: {stats}")
        return stats
    
    def get_followup_count(self, email: str, rule_name: str) -> int:
        """Get the number of follow-ups sent for a contact using a specific rule"""
        if email not in self.followup_history:
            return 0
        
        return sum(1 for f in self.followup_history[email] if f['rule_name'] == rule_name)
    
    def schedule_followup(self, contact: Contact, rule: FollowUpRule):
        """Manually schedule a follow-up for a contact"""
        if contact.email not in self.followup_history:
            self.followup_history[contact.email] = []
        
        followup_date = datetime.now() + timedelta(days=rule.days)
        contact.follow_up_date = followup_date
        logger.info(f"Scheduled follow-up for {contact.email} on {followup_date}")

