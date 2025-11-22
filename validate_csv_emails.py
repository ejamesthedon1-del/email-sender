#!/usr/bin/env python3
"""
Standalone script to validate emails in CSV files
Usage: python validate_csv_emails.py input.csv [output.csv]
"""
import argparse
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.utils.email_validator import validate_emails_in_csv, validate_single_email
from src.utils import setup_logging


def main():
    parser = argparse.ArgumentParser(
        description='Validate emails in a CSV file and create a cleaned CSV with only valid emails',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Validate emails in contacts.csv, output to contacts_validated.csv
  python validate_csv_emails.py contacts.csv contacts_validated.csv
  
  # Validate emails, auto-generate output filename
  python validate_csv_emails.py contacts.csv
  
  # Validate with custom email column name
  python validate_csv_emails.py contacts.csv --email-column EmailAddress
        """
    )
    
    parser.add_argument('input_file', help='Input CSV file path')
    parser.add_argument('output_file', nargs='?', help='Output CSV file path (optional, auto-generated if not provided)')
    parser.add_argument('--email-column', default='email', 
                       help='Name of the email column (default: email)')
    parser.add_argument('--log-level', default='INFO',
                       help='Logging level (default: INFO)')
    
    args = parser.parse_args()
    
    # Setup logging
    setup_logging(args.log_level)
    
    try:
        print(f"\n{'='*60}")
        print(f"Email Validation Utility")
        print(f"{'='*60}")
        print(f"Input file: {args.input_file}")
        if args.output_file:
            print(f"Output file: {args.output_file}")
        print(f"Email column: {args.email_column}")
        print(f"{'='*60}\n")
        
        # Validate emails
        valid_count, invalid_count, output_file = validate_emails_in_csv(
            input_file=args.input_file,
            output_file=args.output_file,
            email_column=args.email_column
        )
        
        # Print results
        print(f"\n{'='*60}")
        print("Validation Results:")
        print(f"{'='*60}")
        print(f"Valid emails:   {valid_count}")
        print(f"Invalid emails: {invalid_count}")
        print(f"Total emails:   {valid_count + invalid_count}")
        
        if output_file:
            print(f"\n✓ Cleaned CSV saved to: {output_file}")
        else:
            print(f"\n⚠ No valid emails found. Output file not created.")
        
        print(f"{'='*60}\n")
        
        return 0 if valid_count > 0 else 1
        
    except FileNotFoundError as e:
        print(f"Error: {str(e)}", file=sys.stderr)
        return 1
    except ValueError as e:
        print(f"Error: {str(e)}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"Unexpected error: {str(e)}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())

