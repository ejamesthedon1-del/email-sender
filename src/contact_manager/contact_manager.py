"""
Contact Manager - Manages leads/contacts for email outreach
"""
import csv
import json
import logging
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass
class Contact:
    """Represents a single contact/lead"""
    email: str
    first_name: str = ""
    last_name: str = ""
    company: str = ""
    brokerage: str = ""
    city: str = ""
    state: str = ""
    custom1: str = ""
    custom2: str = ""
    custom3: str = ""
    custom4: str = ""
    custom5: str = ""
    status: str = "pending"  # pending, sent, replied, bounced, unsubscribed
    sent_count: int = 0
    last_sent_date: Optional[datetime] = None
    follow_up_date: Optional[datetime] = None
    notes: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert contact to dictionary for template variables"""
        data = asdict(self)
        # Convert datetime objects to strings
        if data.get('last_sent_date'):
            data['last_sent_date'] = data['last_sent_date'].isoformat()
        if data.get('follow_up_date'):
            data['follow_up_date'] = data['follow_up_date'].isoformat()
        return data
    
    def get_template_variables(self) -> Dict[str, Any]:
        """Get variables for template rendering"""
        return {
            'FirstName': self.first_name,
            'LastName': self.last_name,
            'FullName': f"{self.first_name} {self.last_name}".strip(),
            'Email': self.email,
            'Company': self.company,
            'Brokerage': self.brokerage,
            'City': self.city,
            'State': self.state,
            'Custom1': self.custom1,
            'Custom2': self.custom2,
            'Custom3': self.custom3,
            'Custom4': self.custom4,
            'Custom5': self.custom5,
        }


class ContactManager:
    """Manages contacts/leads for email outreach"""
    
    def __init__(self, contacts: Optional[List[Contact]] = None):
        self.contacts = contacts or []
    
    def load_from_csv(self, file_path: str, encoding: str = 'utf-8') -> int:
        """
        Load contacts from a CSV file
        
        Expected CSV columns: email, first_name, last_name, company, brokerage, 
        city, state, custom1, custom2, custom3, custom4, custom5
        
        Returns:
            Number of contacts loaded
        """
        contacts = []
        try:
            with open(file_path, 'r', encoding=encoding) as f:
                reader = csv.DictReader(f)
                for row in reader:
                    # Normalize column names (case-insensitive, handle spaces/underscores)
                    normalized_row = {k.lower().strip().replace(' ', '_'): v for k, v in row.items()}
                    
                    contact = Contact(
                        email=normalized_row.get('email', '').strip(),
                        first_name=normalized_row.get('first_name', '').strip(),
                        last_name=normalized_row.get('last_name', '').strip(),
                        company=normalized_row.get('company', '').strip(),
                        brokerage=normalized_row.get('brokerage', '').strip(),
                        city=normalized_row.get('city', '').strip(),
                        state=normalized_row.get('state', '').strip(),
                        custom1=normalized_row.get('custom1', '').strip(),
                        custom2=normalized_row.get('custom2', '').strip(),
                        custom3=normalized_row.get('custom3', '').strip(),
                        custom4=normalized_row.get('custom4', '').strip(),
                        custom5=normalized_row.get('custom5', '').strip(),
                    )
                    
                    if contact.email:  # Only add if email exists
                        contacts.append(contact)
            
            self.contacts = contacts
            logger.info(f"Loaded {len(contacts)} contacts from {file_path}")
            return len(contacts)
            
        except Exception as e:
            logger.error(f"Error loading contacts from CSV: {str(e)}")
            raise
    
    def save_to_csv(self, file_path: str):
        """Save contacts to a CSV file"""
        if not self.contacts:
            logger.warning("No contacts to save")
            return
        
        fieldnames = [
            'email', 'first_name', 'last_name', 'company', 'brokerage',
            'city', 'state', 'custom1', 'custom2', 'custom3', 'custom4', 'custom5',
            'status', 'sent_count', 'last_sent_date', 'follow_up_date', 'notes'
        ]
        
        try:
            with open(file_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                
                for contact in self.contacts:
                    row = contact.to_dict()
                    writer.writerow(row)
            
            logger.info(f"Saved {len(self.contacts)} contacts to {file_path}")
            
        except Exception as e:
            logger.error(f"Error saving contacts to CSV: {str(e)}")
            raise
    
    def get_pending_contacts(self) -> List[Contact]:
        """Get all contacts with pending status"""
        return [c for c in self.contacts if c.status == 'pending']
    
    def get_contacts_for_followup(self, date: Optional[datetime] = None) -> List[Contact]:
        """Get contacts that need follow-up"""
        if date is None:
            date = datetime.now()
        
        return [
            c for c in self.contacts 
            if c.follow_up_date and c.follow_up_date <= date and c.status != 'unsubscribed'
        ]
    
    def update_contact_status(self, email: str, status: str, 
                             notes: Optional[str] = None):
        """Update contact status"""
        for contact in self.contacts:
            if contact.email.lower() == email.lower():
                contact.status = status
                if notes:
                    contact.notes = notes
                return
        
        logger.warning(f"Contact not found: {email}")
    
    def mark_as_sent(self, email: str):
        """Mark a contact as sent"""
        for contact in self.contacts:
            if contact.email.lower() == email.lower():
                contact.status = 'sent'
                contact.sent_count += 1
                contact.last_sent_date = datetime.now()
                return
        
        logger.warning(f"Contact not found: {email}")
    
    def add_contact(self, contact: Contact):
        """Add a new contact"""
        # Check if contact already exists
        for existing in self.contacts:
            if existing.email.lower() == contact.email.lower():
                logger.warning(f"Contact already exists: {contact.email}")
                return
        
        self.contacts.append(contact)
    
    def get_contact(self, email: str) -> Optional[Contact]:
        """Get a contact by email"""
        for contact in self.contacts:
            if contact.email.lower() == email.lower():
                return contact
        return None
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get statistics about contacts"""
        total = len(self.contacts)
        status_counts = {}
        for contact in self.contacts:
            status_counts[contact.status] = status_counts.get(contact.status, 0) + 1
        
        return {
            'total': total,
            'by_status': status_counts,
            'pending': len(self.get_pending_contacts()),
            'sent': status_counts.get('sent', 0),
        }

