"""
Unit tests for PHI Pattern Detection
Tests the Patterns class from src/patterns.py
"""

import pytest
import sys
from pathlib import Path

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from patterns import Patterns


class TestPatterns:
    """Test suite for the Patterns class"""

    @pytest.fixture
    def detector(self):
        """Create a Patterns instance for testing"""
        return Patterns()

    # Tests for detect_sin()
    def test_detect_sin_with_dashes(self, detector):
        """Test SIN detection with dash format"""
        text = "My SIN is 123-456-789"
        results = detector.detect_sin(text)

        assert len(results) == 1
        assert results[0]['type'] == 'Social Insurance Number (SIN)'
        assert results[0]['value'] == '123-456-789'
        assert results[0]['confidence'] == 0.85
        assert results[0]['hipaa_identifier'] == 'National identification number'

    def test_detect_sin_with_spaces(self, detector):
        """Test SIN detection with space format"""
        text = "SIN: 987 654 321"
        results = detector.detect_sin(text)

        assert len(results) == 1
        assert results[0]['value'] == '987 654 321'

    def test_detect_sin_no_separator(self, detector):
        """Test SIN detection without separators"""
        text = "SIN: 111222333"
        results = detector.detect_sin(text)

        assert len(results) == 1
        assert results[0]['value'] == '111222333'

    def test_detect_sin_rejects_all_same_digits(self, detector):
        """Test that SIN rejects numbers with all same digits"""
        text = "Invalid: 111-111-111"
        results = detector.detect_sin(text)

        assert len(results) == 0

    def test_detect_sin_multiple(self, detector):
        """Test detection of multiple SINs"""
        text = "First: 123-456-789, Second: 987-654-321"
        results = detector.detect_sin(text)

        assert len(results) == 2

    # Tests for detect_phn()
    def test_detect_phn_with_context(self, detector):
        """Test PHN detection with context keywords"""
        text = "PHN: 1234567890 for patient"
        results = detector.detect_phn(text)

        assert len(results) == 1
        assert results[0]['type'] == 'Personal Health Number (PHN)'
        assert results[0]['value'] == '1234567890'
        assert results[0]['confidence'] == 0.9  # High confidence due to 'PHN' keyword
        assert results[0]['hipaa_identifier'] == 'Health plan beneficiary number'

    def test_detect_phn_without_context(self, detector):
        """Test PHN detection without context keywords"""
        text = "Number: 9876543210 in record"
        results = detector.detect_phn(text)

        assert len(results) == 1
        assert results[0]['confidence'] == 0.5  # Low confidence without keywords

    def test_detect_phn_with_health_number_keyword(self, detector):
        """Test PHN with 'health number' keyword"""
        text = "health number is 5555555555"
        results = detector.detect_phn(text)

        assert len(results) == 1
        assert results[0]['confidence'] == 0.9

    # Tests for detect_phone()
    def test_detect_phone_parentheses_format(self, detector):
        """Test phone detection with (###) ###-#### format"""
        text = "Call me at (604) 555-1234"
        results = detector.detect_phone(text)

        assert len(results) == 1
        assert results[0]['type'] == 'Phone Number'
        assert results[0]['value'] == '(604) 555-1234'
        assert results[0]['confidence'] == 0.8
        assert results[0]['hipaa_identifier'] == 'Telephone number'

    def test_detect_phone_dash_format(self, detector):
        """Test phone detection with ###-###-#### format"""
        text = "Phone: 604-555-9999"
        results = detector.detect_phone(text)

        assert len(results) == 1
        assert results[0]['value'] == '604-555-9999'

    def test_detect_phone_dot_format(self, detector):
        """Test phone detection with ###.###.#### format"""
        text = "Contact: 250.555.7777"
        results = detector.detect_phone(text)

        assert len(results) == 1
        assert results[0]['value'] == '250.555.7777'

    def test_detect_phone_multiple_formats(self, detector):
        """Test detection of multiple phone formats"""
        text = "Office: (604) 555-0000, Cell: 778-555-1111, Fax: 604.555.2222"
        results = detector.detect_phone(text)

        assert len(results) == 3

    # Tests for detect_email()
    def test_detect_email_basic(self, detector):
        """Test basic email detection"""
        text = "Contact: john.doe@example.com"
        results = detector.detect_email(text)

        assert len(results) == 1
        assert results[0]['type'] == 'Email Address'
        assert results[0]['value'] == 'john.doe@example.com'
        assert results[0]['confidence'] == 0.95
        assert results[0]['hipaa_identifier'] == 'Email address'

    def test_detect_email_with_numbers(self, detector):
        """Test email with numbers"""
        text = "user123@domain456.ca"
        results = detector.detect_email(text)

        assert len(results) == 1
        assert results[0]['value'] == 'user123@domain456.ca'

    def test_detect_email_with_special_chars(self, detector):
        """Test email with special characters"""
        text = "test.user+tag@sub.example.org"
        results = detector.detect_email(text)

        assert len(results) == 1
        assert results[0]['value'] == 'test.user+tag@sub.example.org'

    def test_detect_email_multiple(self, detector):
        """Test detection of multiple emails"""
        text = "From: alice@example.com To: bob@test.org"
        results = detector.detect_email(text)

        assert len(results) == 2

    # Tests for detect_credit_card()
    def test_detect_credit_card_valid_luhn(self, detector):
        """Test credit card with valid Luhn checksum"""
        # Valid test card number: 4532015112830366
        text = "Card: 4532015112830366"
        results = detector.detect_credit_card(text)

        assert len(results) == 1
        assert results[0]['type'] == 'Credit Card Number'
        assert results[0]['value'] == '4532015112830366'
        assert results[0]['confidence'] == 0.9

    def test_detect_credit_card_with_dashes(self, detector):
        """Test credit card with dashes"""
        # Valid test card: 4532-0151-1283-0366
        text = "Payment: 4532-0151-1283-0366"
        results = detector.detect_credit_card(text)

        assert len(results) == 1
        assert results[0]['value'] == '4532-0151-1283-0366'

    def test_detect_credit_card_with_spaces(self, detector):
        """Test credit card with spaces"""
        text = "CC: 4532 0151 1283 0366"
        results = detector.detect_credit_card(text)

        assert len(results) == 1
        assert results[0]['value'] == '4532 0151 1283 0366'

    def test_detect_credit_card_invalid_luhn(self, detector):
        """Test that invalid Luhn checksum is rejected"""
        text = "Invalid: 1234567890123456"
        results = detector.detect_credit_card(text)

        assert len(results) == 0

    # Tests for detect_postal_code()
    def test_detect_postal_code_with_space(self, detector):
        """Test Canadian postal code with space"""
        text = "Address: V6B 1A1"
        results = detector.detect_postal_code(text)

        assert len(results) == 1
        assert results[0]['type'] == 'Postal Code'
        assert results[0]['value'] == 'V6B 1A1'
        assert results[0]['confidence'] == 0.85
        assert results[0]['hipaa_identifier'] == 'Geographic subdivision (postal code)'

    def test_detect_postal_code_without_space(self, detector):
        """Test Canadian postal code without space"""
        text = "Postal: M5H2N2"
        results = detector.detect_postal_code(text)

        assert len(results) == 1
        assert results[0]['value'] == 'M5H2N2'

    def test_detect_postal_code_lowercase(self, detector):
        """Test postal code with lowercase letters"""
        text = "Located at v6b 1a1"
        results = detector.detect_postal_code(text)

        assert len(results) == 1
        assert results[0]['value'] == 'v6b 1a1'

    def test_detect_postal_code_multiple(self, detector):
        """Test detection of multiple postal codes"""
        text = "From V5K 1A1 to V6B 2B2"
        results = detector.detect_postal_code(text)

        assert len(results) == 2

    # Tests for detect_ip()
    def test_detect_ip_valid(self, detector):
        """Test valid IP address detection"""
        text = "Server: 192.168.1.1"
        results = detector.detect_ip(text)

        assert len(results) == 1
        assert results[0]['type'] == 'IP Address'
        assert results[0]['value'] == '192.168.1.1'
        assert results[0]['confidence'] == 0.9
        assert results[0]['hipaa_identifier'] == 'IP address'

    def test_detect_ip_public(self, detector):
        """Test public IP address"""
        text = "IP: 8.8.8.8"
        results = detector.detect_ip(text)

        assert len(results) == 1
        assert results[0]['value'] == '8.8.8.8'

    def test_detect_ip_invalid_range(self, detector):
        """Test that IP with invalid octet is rejected"""
        text = "Invalid: 192.168.256.1"
        results = detector.detect_ip(text)

        assert len(results) == 0

    def test_detect_ip_edge_cases(self, detector):
        """Test IP with edge case values"""
        text = "IPs: 0.0.0.0 and 255.255.255.255"
        results = detector.detect_ip(text)

        assert len(results) == 2

    def test_detect_ip_multiple(self, detector):
        """Test detection of multiple IPs"""
        text = "Primary: 10.0.0.1, Secondary: 10.0.0.2"
        results = detector.detect_ip(text)

        assert len(results) == 2

    # Tests for detect_date()
    def test_detect_date_slash_format(self, detector):
        """Test date with MM/DD/YYYY format"""
        text = "DOB: 01/15/1990"
        results = detector.detect_date(text)

        assert len(results) == 1
        assert results[0]['type'] == 'Date'
        assert results[0]['value'] == '01/15/1990'
        assert results[0]['confidence'] == 0.7
        assert results[0]['hipaa_identifier'] == 'Date element'

    def test_detect_date_iso_format(self, detector):
        """Test date with YYYY-MM-DD format"""
        text = "Date: 2024-03-15"
        results = detector.detect_date(text)

        assert len(results) == 1
        assert results[0]['value'] == '2024-03-15'

    def test_detect_date_dash_format(self, detector):
        """Test date with DD-MM-YYYY format"""
        text = "Appointment: 15-03-2024"
        results = detector.detect_date(text)

        assert len(results) == 1
        assert results[0]['value'] == '15-03-2024'

    def test_detect_date_single_digit(self, detector):
        """Test date with single digit day/month"""
        text = "Date: 1/5/2024"
        results = detector.detect_date(text)

        assert len(results) == 1
        assert results[0]['value'] == '1/5/2024'

    def test_detect_date_multiple(self, detector):
        """Test detection of multiple dates"""
        text = "From 01/01/2024 to 12/31/2024"
        results = detector.detect_date(text)

        assert len(results) == 2

    # Tests for detect_all()
    def test_detect_all_comprehensive(self, detector):
        """Test detect_all with comprehensive PHI"""
        text = """
        Patient: John Doe
        SIN: 123-456-789
        PHN: 9876543210
        Phone: (604) 555-1234
        Email: john.doe@example.com
        Address: 123 Main St, Vancouver, BC V6B 1A1
        DOB: 01/15/1980
        IP: 192.168.1.1
        """
        results = detector.detect_all(text)

        # Should detect SIN, PHN, Phone, Email, Postal Code, Date, and IP
        assert len(results) >= 6

        # Verify results are sorted by position
        positions = [r['start'] for r in results]
        assert positions == sorted(positions)

    def test_detect_all_removes_duplicates(self, detector):
        """Test that detect_all removes duplicate detections"""
        text = "Test 1234567890 number"
        results = detector.detect_all(text)

        # Should only have one instance even if detected by multiple methods
        positions = [(r['start'], r['end'], r['type']) for r in results]
        assert len(positions) == len(set(positions))

    def test_detect_all_empty_text(self, detector):
        """Test detect_all with empty text"""
        results = detector.detect_all("")

        assert results == []

    def test_detect_all_no_phi(self, detector):
        """Test detect_all with text containing no PHI"""
        text = "This is just regular text with no sensitive information."
        results = detector.detect_all(text)

        assert len(results) == 0

    # Tests for _luhn_check()
    def test_luhn_check_valid(self, detector):
        """Test Luhn algorithm with valid card number"""
        # Valid test card numbers
        assert detector._luhn_check("4532015112830366") == True
        assert detector._luhn_check("5425233430109903") == True

    def test_luhn_check_invalid(self, detector):
        """Test Luhn algorithm with invalid card number"""
        assert detector._luhn_check("1234567890123456") == False
        assert detector._luhn_check("1111111111111111") == False

    def test_luhn_check_edge_cases(self, detector):
        """Test Luhn algorithm edge cases"""
        # All zeros
        assert detector._luhn_check("0000000000000000") == True

    # Tests for position tracking
    def test_position_tracking(self, detector):
        """Test that positions are correctly tracked"""
        text = "Email: test@example.com in the middle"
        results = detector.detect_email(text)

        assert len(results) == 1
        assert results[0]['start'] == 7
        assert results[0]['end'] == 23
        assert text[results[0]['start']:results[0]['end']] == results[0]['value']

    def test_multiple_detections_positions(self, detector):
        """Test positions with multiple detections"""
        text = "Phone: 604-555-1234 and email: test@example.com"
        results = detector.detect_all(text)

        # Verify all positions are correct
        for result in results:
            extracted = text[result['start']:result['end']]
            assert extracted == result['value']


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v"])
