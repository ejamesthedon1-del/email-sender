"""
Email Validation Utility - Isolated function for validating emails in CSV files
"""
import csv
import logging
from typing import Tuple, List
from pathlib import Path
from email_validator import validate_email, EmailNotValidError

logger = logging.getLogger(__name__)


def validate_emails_in_csv(input_file: str, output_file: str = None, 
                           email_column: str = 'email', encoding: str = 'utf-8') -> Tuple[int, int, str]:
    """
    Validate emails in a CSV file and create a cleaned CSV with only valid emails.
    
    This function is completely isolated and does not modify any existing functionality.
    
    Args:
        input_file: Path to input CSV file
        output_file: Path to output CSV file (if None, adds '_validated' suffix to input filename)
        email_column: Name of the column containing email addresses (default: 'email')
        encoding: File encoding (default: 'utf-8')
    
    Returns:
        Tuple of (valid_count, invalid_count, output_file_path)
    
    Example:
        valid, invalid, output = validate_emails_in_csv('contacts.csv', 'contacts_validated.csv')
        print(f"Valid: {valid}, Invalid: {invalid}, Output: {output}")
    """
    input_path = Path(input_file)
    
    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_file}")
    
    # Generate output filename if not provided
    if output_file is None:
        output_path = input_path.parent / f"{input_path.stem}_validated{input_path.suffix}"
    else:
        output_path = Path(output_file)
    
    valid_count = 0
    invalid_count = 0
    valid_rows = []
    invalid_emails = []
    
    logger.info(f"Starting email validation for: {input_file}")
    
    try:
        # Read input CSV
        with open(input_path, 'r', encoding=encoding) as f:
            reader = csv.DictReader(f)
            
            # Get all fieldnames
            fieldnames = reader.fieldnames
            if not fieldnames:
                raise ValueError("CSV file has no headers")
            
            # Normalize column names (case-insensitive)
            normalized_fieldnames = {name.lower().strip().replace(' ', '_'): name for name in fieldnames}
            
            # Find email column (case-insensitive and flexible matching)
            email_col_key = None
            email_col_name = None
            
            # Normalize the requested email_column for comparison
            requested_key = email_column.lower().strip().replace(' ', '_')
            
            # First try exact match with normalized fieldnames
            for key, original_name in normalized_fieldnames.items():
                if key == requested_key:
                    email_col_key = key
                    email_col_name = original_name
                    logger.debug(f"Found exact match for email column: {email_col_name}")
                    break
            
            # If no exact match, try to find any column containing 'email'
            if not email_col_key:
                for key, original_name in normalized_fieldnames.items():
                    if 'email' in key:
                        email_col_key = key
                        email_col_name = original_name
                        logger.debug(f"Found email column by keyword match: {email_col_name}")
                        break
            
            # Last resort: try case-insensitive match on original column names
            if not email_col_key:
                for original_name in fieldnames:
                    if original_name.lower().strip().replace(' ', '_') == requested_key:
                        email_col_name = original_name
                        email_col_key = requested_key
                        logger.debug(f"Found email column by case-insensitive match: {email_col_name}")
                        break
            
            if not email_col_key:
                raise ValueError(f"Email column '{email_column}' not found in CSV. Available columns: {list(fieldnames)}")
            
            logger.info(f"Using email column: '{email_col_name}' (requested: '{email_column}')")
            
            # Process each row
            for row_num, row in enumerate(reader, start=2):  # Start at 2 (row 1 is header)
                email = row.get(email_col_name, '').strip()
                
                if not email:
                    invalid_count += 1
                    invalid_emails.append(f"Row {row_num}: (empty)")
                    continue
                
                # Validate email
                try:
                    # Validate and normalize email
                    validation = validate_email(email, check_deliverability=False)
                    normalized_email = validation.email
                    
                    # Update row with normalized email
                    row[email_col_name] = normalized_email
                    valid_rows.append(row)
                    valid_count += 1
                    
                except EmailNotValidError as e:
                    invalid_count += 1
                    invalid_emails.append(f"Row {row_num}: {email} - {str(e)}")
                    logger.debug(f"Invalid email at row {row_num}: {email} - {str(e)}")
                except Exception as e:
                    invalid_count += 1
                    invalid_emails.append(f"Row {row_num}: {email} - Unexpected error: {str(e)}")
                    logger.error(f"Error validating email at row {row_num}: {email} - {str(e)}")
        
        # Write output CSV with only valid emails
        if valid_rows:
            with open(output_path, 'w', newline='', encoding=encoding) as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(valid_rows)
            
            logger.info(f"Validation complete. Valid: {valid_count}, Invalid: {invalid_count}")
            logger.info(f"Output saved to: {output_path}")
        else:
            logger.warning("No valid emails found. Output file not created.")
            output_path = None
        
        # Log invalid emails summary
        if invalid_emails:
            logger.info(f"Invalid emails ({invalid_count}):")
            for invalid in invalid_emails[:10]:  # Show first 10
                logger.info(f"  - {invalid}")
            if len(invalid_emails) > 10:
                logger.info(f"  ... and {len(invalid_emails) - 10} more")
        
        return (valid_count, invalid_count, str(output_path) if output_path else None)
        
    except Exception as e:
        logger.error(f"Error processing CSV file: {str(e)}")
        raise


def validate_single_email(email: str) -> Tuple[bool, str]:
    """
    Validate a single email address.
    
    Args:
        email: Email address to validate
    
    Returns:
        Tuple of (is_valid, normalized_email_or_error_message)
    
    Example:
        is_valid, result = validate_single_email("test@example.com")
        if is_valid:
            print(f"Valid: {result}")
        else:
            print(f"Invalid: {result}")
    """
    if not email or not email.strip():
        return (False, "Email is empty")
    
    try:
        validation = validate_email(email.strip(), check_deliverability=False)
        return (True, validation.email)
    except EmailNotValidError as e:
        return (False, str(e))
    except Exception as e:
        return (False, f"Validation error: {str(e)}")

