#!/usr/bin/env python3
"""
Example usage of the email validation utility
"""
from src.utils.email_validator import validate_emails_in_csv, validate_single_email

# Example 1: Validate emails in a CSV file
if __name__ == '__main__':
    print("Email Validation Utility Examples\n")
    
    # Example 1: Validate a single email
    print("Example 1: Validate single email")
    print("-" * 50)
    is_valid, result = validate_single_email("test@example.com")
    if is_valid:
        print(f"✓ Valid: {result}")
    else:
        print(f"✗ Invalid: {result}")
    
    is_valid, result = validate_single_email("invalid-email")
    if is_valid:
        print(f"✓ Valid: {result}")
    else:
        print(f"✗ Invalid: {result}")
    
    print("\n" + "=" * 50 + "\n")
    
    # Example 2: Validate CSV file
    print("Example 2: Validate emails in CSV file")
    print("-" * 50)
    print("Usage: validate_emails_in_csv('contacts.csv', 'contacts_validated.csv')")
    print("\nThis will:")
    print("  1. Read the input CSV file")
    print("  2. Validate all emails in the 'email' column")
    print("  3. Create a new CSV with only valid emails")
    print("  4. Return (valid_count, invalid_count, output_file_path)")
    
    # Uncomment to actually run:
    # valid, invalid, output = validate_emails_in_csv(
    #     input_file='examples/contacts.csv',
    #     output_file='examples/contacts_validated.csv'
    # )
    # print(f"\nResults: Valid={valid}, Invalid={invalid}, Output={output}")

