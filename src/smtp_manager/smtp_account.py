"""
SMTP Account Manager - Handles multiple SMTP accounts with rotation
"""
import smtplib
import ssl
import logging
from typing import List, Dict, Optional
from dataclasses import dataclass
from datetime import datetime, timedelta
import time

logger = logging.getLogger(__name__)


@dataclass
class SMTPAccount:
    """Represents a single SMTP account configuration"""
    name: str
    host: str
    port: int
    username: str
    password: str
    from_email: str
    from_name: str = ""
    use_tls: bool = True
    use_ssl: bool = False
    daily_limit: int = 500  # Daily sending limit
    hourly_limit: int = 50  # Hourly sending limit
    delay_between_emails: float = 2.0  # Seconds between emails
    
    def __post_init__(self):
        self.sent_today = 0
        self.sent_this_hour = 0
        self.last_reset_date = datetime.now().date()
        self.last_reset_hour = datetime.now().replace(minute=0, second=0, microsecond=0)
        self.last_sent_time = None
        self.is_active = True
        self.failure_count = 0
        self.max_failures = 5


class SMTPManager:
    """Manages multiple SMTP accounts with rotation and rate limiting"""
    
    def __init__(self, accounts: List[SMTPAccount]):
        self.accounts = accounts
        self.current_index = 0
        self.connections: Dict[str, Optional[smtplib.SMTP]] = {}
        self._reset_limits_if_needed()
    
    def _reset_limits_if_needed(self):
        """Reset daily/hourly limits if time period has passed"""
        now = datetime.now()
        current_date = now.date()
        current_hour = now.replace(minute=0, second=0, microsecond=0)
        
        for account in self.accounts:
            # Reset daily limit
            if current_date > account.last_reset_date:
                account.sent_today = 0
                account.last_reset_date = current_date
            
            # Reset hourly limit
            if current_hour > account.last_reset_hour:
                account.sent_this_hour = 0
                account.last_reset_hour = current_hour
    
    def get_available_account(self) -> Optional[SMTPAccount]:
        """Get the next available SMTP account using round-robin rotation"""
        self._reset_limits_if_needed()
        
        # Try to find an available account
        attempts = 0
        while attempts < len(self.accounts):
            account = self.accounts[self.current_index]
            self.current_index = (self.current_index + 1) % len(self.accounts)
            
            if self._is_account_available(account):
                return account
            
            attempts += 1
        
        # No available accounts
        logger.warning("No available SMTP accounts. All accounts have reached their limits.")
        return None
    
    def _is_account_available(self, account: SMTPAccount) -> bool:
        """Check if an account is available for sending"""
        if not account.is_active:
            return False
        
        if account.sent_today >= account.daily_limit:
            logger.debug(f"Account {account.name} has reached daily limit")
            return False
        
        if account.sent_this_hour >= account.hourly_limit:
            logger.debug(f"Account {account.name} has reached hourly limit")
            return False
        
        # Check if enough time has passed since last email
        if account.last_sent_time:
            time_since_last = (datetime.now() - account.last_sent_time).total_seconds()
            if time_since_last < account.delay_between_emails:
                return False
        
        return True
    
    def get_connection(self, account: SMTPAccount) -> Optional[smtplib.SMTP]:
        """Get or create an SMTP connection for an account"""
        if account.name in self.connections and self.connections[account.name]:
            try:
                # Test if connection is still alive
                self.connections[account.name].noop()
                return self.connections[account.name]
            except:
                # Connection is dead, remove it
                self.connections[account.name] = None
        
        try:
            if account.use_ssl:
                context = ssl.create_default_context()
                server = smtplib.SMTP_SSL(account.host, account.port, context=context)
            else:
                server = smtplib.SMTP(account.host, account.port)
            
            if account.use_tls and not account.use_ssl:
                server.starttls()
            
            server.login(account.username, account.password)
            self.connections[account.name] = server
            logger.info(f"Connected to SMTP server for account: {account.name}")
            return server
        except Exception as e:
            logger.error(f"Failed to connect to SMTP server for {account.name}: {str(e)}")
            account.failure_count += 1
            if account.failure_count >= account.max_failures:
                account.is_active = False
                logger.warning(f"Account {account.name} deactivated due to repeated failures")
            return None
    
    def send_email(self, account: SMTPAccount, to_email: str, subject: str, 
                   body: str, html_body: Optional[str] = None) -> bool:
        """Send an email using the specified account"""
        connection = self.get_connection(account)
        if not connection:
            return False
        
        try:
            from email.mime.text import MIMEText
            from email.mime.multipart import MIMEMultipart
            
            msg = MIMEMultipart('alternative')
            msg['From'] = f"{account.from_name} <{account.from_email}>" if account.from_name else account.from_email
            msg['To'] = to_email
            msg['Subject'] = subject
            
            # Add plain text and HTML parts
            # Only attach plain text if it's not empty
            if body and body.strip():
                msg.attach(MIMEText(body, 'plain'))
            if html_body and html_body.strip():
                msg.attach(MIMEText(html_body, 'html'))
            
            # Ensure at least one part is attached
            if not (body and body.strip()) and not (html_body and html_body.strip()):
                raise ValueError("Either plain text body or HTML body must be provided")
            
            connection.send_message(msg)
            
            # Update account statistics
            account.sent_today += 1
            account.sent_this_hour += 1
            account.last_sent_time = datetime.now()
            account.failure_count = 0  # Reset on success
            
            logger.info(f"Email sent successfully from {account.name} to {to_email}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send email from {account.name} to {to_email}: {str(e)}")
            account.failure_count += 1
            if account.failure_count >= account.max_failures:
                account.is_active = False
                logger.warning(f"Account {account.name} deactivated due to repeated failures")
            return False
    
    def close_all_connections(self):
        """Close all SMTP connections"""
        for name, connection in self.connections.items():
            if connection:
                try:
                    connection.quit()
                except:
                    pass
        self.connections.clear()
        logger.info("All SMTP connections closed")
    
    def get_account_stats(self) -> Dict[str, Dict]:
        """Get statistics for all accounts"""
        stats = {}
        for account in self.accounts:
            stats[account.name] = {
                'sent_today': account.sent_today,
                'sent_this_hour': account.sent_this_hour,
                'daily_limit': account.daily_limit,
                'hourly_limit': account.hourly_limit,
                'is_active': account.is_active,
                'failure_count': account.failure_count
            }
        return stats

