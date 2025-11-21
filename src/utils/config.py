"""
Configuration Management
"""
import os
from typing import List, Dict, Any
from dotenv import load_dotenv
import logging

from ..smtp_manager import SMTPAccount

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)


def load_smtp_accounts_from_env() -> List[SMTPAccount]:
    """
    Load SMTP accounts from environment variables
    
    Supports multiple accounts with naming like:
    SMTP_HOST_1, SMTP_PORT_1, SMTP_USERNAME_1, etc.
    Or single account: SMTP_HOST, SMTP_PORT, etc.
    """
    accounts = []
    
    # Try to load multiple accounts (numbered)
    account_num = 1
    while True:
        host = os.getenv(f'SMTP_HOST_{account_num}') or (os.getenv('SMTP_HOST') if account_num == 1 else None)
        if not host:
            break
        
        port = int(os.getenv(f'SMTP_PORT_{account_num}', os.getenv('SMTP_PORT', '587')))
        username = os.getenv(f'SMTP_USERNAME_{account_num}') or os.getenv('SMTP_USERNAME', '')
        password = os.getenv(f'SMTP_PASSWORD_{account_num}') or os.getenv('SMTP_PASSWORD', '')
        from_email = os.getenv(f'SMTP_FROM_EMAIL_{account_num}') or os.getenv('SMTP_FROM_EMAIL', username)
        from_name = os.getenv(f'SMTP_FROM_NAME_{account_num}') or os.getenv('SMTP_FROM_NAME', '')
        
        use_tls = os.getenv(f'SMTP_USE_TLS_{account_num}', os.getenv('SMTP_USE_TLS', 'true')).lower() == 'true'
        use_ssl = os.getenv(f'SMTP_USE_SSL_{account_num}', os.getenv('SMTP_USE_SSL', 'false')).lower() == 'true'
        
        daily_limit = int(os.getenv(f'SMTP_DAILY_LIMIT_{account_num}', os.getenv('SMTP_DAILY_LIMIT', '500')))
        hourly_limit = int(os.getenv(f'SMTP_HOURLY_LIMIT_{account_num}', os.getenv('SMTP_HOURLY_LIMIT', '50')))
        delay = float(os.getenv(f'SMTP_DELAY_{account_num}', os.getenv('SMTP_DELAY', '2.0')))
        
        account = SMTPAccount(
            name=f"Account_{account_num}" if account_num > 1 else "Account_1",
            host=host,
            port=port,
            username=username,
            password=password,
            from_email=from_email,
            from_name=from_name,
            use_tls=use_tls,
            use_ssl=use_ssl,
            daily_limit=daily_limit,
            hourly_limit=hourly_limit,
            delay_between_emails=delay
        )
        
        accounts.append(account)
        account_num += 1
        
        # If we found account 1 and it's not numbered, break (single account mode)
        if account_num == 2 and not os.getenv('SMTP_HOST_2'):
            break
    
    if not accounts:
        logger.warning("No SMTP accounts found in environment variables")
    
    return accounts


def setup_logging(log_level: str = "INFO", log_file: str = None):
    """Setup logging configuration"""
    level = getattr(logging, log_level.upper(), logging.INFO)
    
    handlers = [logging.StreamHandler()]
    if log_file:
        handlers.append(logging.FileHandler(log_file))
    
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=handlers,
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    logger.info(f"Logging configured at {log_level} level")

