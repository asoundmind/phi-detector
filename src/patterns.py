"""
PHI Pattern Detection for British Columbia, Canada
Detects Protected Health Information (PHI) using regex patterns adapted for Canadian standards.
"""

import re
from typing import List, Dict


class Patterns:
    """
    Detects Protected Health Information (PHI) in text using regex patterns.
    Adapted for British Columbia, Canada standards including SIN, PHN, postal codes, etc.
    """
    
    def __init__(self):
        """Initialize regex patterns for Canadian PHI detection."""
        # Social Insurance Number (SIN): ###-###-### or ### ### ###
        self.sin_pattern = re.compile(r'\b\d{3}[-\s]?\d{3}[-\s]?\d{3}\b')
        
        # BC Personal Health Number (PHN): 10 digits
        self.phn_pattern = re.compile(r'\b\d{10}\b')
        
        # Canadian phone numbers: (###) ###-####, ###-###-####, ###.###.####
        self.phone_pattern = re.compile(
            r'(?:\(\d{3}\)\s+\d{3}[-]\d{4}|\b\d{3}[-]\d{3}[-]\d{4}|\b\d{3}[.]\d{3}[.]\d{4})\b'
        )
        
        # Email addresses
        self.email_pattern = re.compile(
            r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        )
        
        # Credit card numbers: 16 digits with optional spaces/dashes
        self.credit_card_pattern = re.compile(
            r'\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b'
        )
        
        # Canadian Postal Code: A1A 1A1 or A1A1A1
        self.postal_code_pattern = re.compile(
            r'\b[A-Z]\d[A-Z]\s?\d[A-Z]\d\b',
            re.IGNORECASE
        )
    
        # IP addresses
        self.ip_pattern = re.compile(
            r'\b(?:\d{1,3}\.){3}\d{1,3}\b'
        )
        
        # Dates: MM/DD/YYYY, YYYY-MM-DD, DD-MM-YYYY, DD/MM/YYYY
        self.date_pattern = re.compile(
            r'\b(?:\d{1,2}[-/]\d{1,2}[-/]\d{4}|\d{4}[-/]\d{1,2}[-/]\d{1,2})\b'
        )
        
    def detect_sin(self, text: str) -> List[Dict]:
        """
        Detect Social Insurance Numbers (SIN) in Canadian format.
        
        Args:
            text: Input text to search
            
        Returns:
            List of dictionaries containing detection results
        """
        results = []
        for match in self.sin_pattern.finditer(text):
            # Basic validation: check if it's not all same digits
            clean_sin = match.group().replace('-', '').replace(' ', '')
            if len(set(clean_sin)) > 1:  # Not all same digit
                results.append({
                    'type': 'Social Insurance Number (SIN)',
                    'value': match.group(),
                    'start': match.start(),
                    'end': match.end(),
                    'confidence': 0.85,
                    'hipaa_identifier': 'National identification number'
                })
        return results
    
    def detect_phn(self, text: str) -> List[Dict]:
        """
        Detect BC Personal Health Numbers (PHN).
        
        Args:
            text: Input text to search
            
        Returns:
            List of dictionaries containing detection results
        """
        results = []
        for match in self.phn_pattern.finditer(text):
            # Check context for PHN-related keywords
            start = max(0, match.start() - 20)
            end = min(len(text), match.end() + 20)
            context = text[start:end].lower()
            
            confidence = 0.5
            if any(keyword in context for keyword in ['phn', 'health number', 'care card', 'bc health']):
                confidence = 0.9
            
            results.append({
                'type': 'Personal Health Number (PHN)',
                'value': match.group(),
                'start': match.start(),
                'end': match.end(),
                'confidence': confidence,
                'hipaa_identifier': 'Health plan beneficiary number'
            })
        return results
    
    def detect_phone(self, text: str) -> List[Dict]:
        """
        Detect Canadian phone numbers in various formats.
        
        Args:
            text: Input text to search
            
        Returns:
            List of dictionaries containing detection results
        """
        results = []
        for match in self.phone_pattern.finditer(text):
            results.append({
                'type': 'Phone Number',
                'value': match.group(),
                'start': match.start(),
                'end': match.end(),
                'confidence': 0.8,
                'hipaa_identifier': 'Telephone number'
            })
        return results
    
    def detect_email(self, text: str) -> List[Dict]:
        """
        Detect email addresses.
        
        Args:
            text: Input text to search
            
        Returns:
            List of dictionaries containing detection results
        """
        results = []
        for match in self.email_pattern.finditer(text):
            results.append({
                'type': 'Email Address',
                'value': match.group(),
                'start': match.start(),
                'end': match.end(),
                'confidence': 0.95,
                'hipaa_identifier': 'Email address'
            })
        return results
    
    def detect_credit_card(self, text: str) -> List[Dict]:
        """
        Detect credit card numbers (16 digits with optional separators).
        
        Args:
            text: Input text to search
            
        Returns:
            List of dictionaries containing detection results
        """
        results = []
        for match in self.credit_card_pattern.finditer(text):
            # Basic Luhn algorithm check
            clean_number = match.group().replace('-', '').replace(' ', '')
            if self._luhn_check(clean_number):
                results.append({
                    'type': 'Credit Card Number',
                    'value': match.group(),
                    'start': match.start(),
                    'end': match.end(),
                    'confidence': 0.9,
                    'hipaa_identifier': 'Account number'
                })
        return results
    
    def detect_postal_code(self, text: str) -> List[Dict]:
        """
        Detect Canadian postal codes (e.g., V6B 1A1).
        
        Args:
            text: Input text to search
            
        Returns:
            List of dictionaries containing detection results
        """
        results = []
        for match in self.postal_code_pattern.finditer(text):
            results.append({
                'type': 'Postal Code',
                'value': match.group(),
                'start': match.start(),
                'end': match.end(),
                'confidence': 0.85,
                'hipaa_identifier': 'Geographic subdivision (postal code)'
            })
        return results
    
    def detect_ip(self, text: str) -> List[Dict]:
        """
        Detect IP addresses.
        
        Args:
            text: Input text to search
            
        Returns:
            List of dictionaries containing detection results
        """
        results = []
        for match in self.ip_pattern.finditer(text):
            # Validate IP address ranges (0-255)
            octets = match.group().split('.')
            if all(0 <= int(octet) <= 255 for octet in octets):
                results.append({
                    'type': 'IP Address',
                    'value': match.group(),
                    'start': match.start(),
                    'end': match.end(),
                    'confidence': 0.9,
                    'hipaa_identifier': 'IP address'
                })
        return results
    
    def detect_date(self, text: str) -> List[Dict]:
        """
        Detect dates in various formats.
        
        Args:
            text: Input text to search
            
        Returns:
            List of dictionaries containing detection results
        """
        results = []
        for match in self.date_pattern.finditer(text):
            results.append({
                'type': 'Date',
                'value': match.group(),
                'start': match.start(),
                'end': match.end(),
                'confidence': 0.7,
                'hipaa_identifier': 'Date element'
            })
        return results
    
    def detect_all(self, text: str) -> List[Dict]:
        """
        Run all PHI detection methods and return combined results sorted by position.
        
        Args:
            text: Input text to search
            
        Returns:
            List of all detected PHI elements sorted by start position
        """
        all_results = []
        
        # Run all detection methods
        all_results.extend(self.detect_sin(text))
        all_results.extend(self.detect_phn(text))
        all_results.extend(self.detect_phone(text))
        all_results.extend(self.detect_email(text))
        all_results.extend(self.detect_credit_card(text))
        all_results.extend(self.detect_postal_code(text))
        all_results.extend(self.detect_ip(text))
        all_results.extend(self.detect_date(text))
        
        # Remove duplicates (same position and type)
        unique_results = []
        seen = set()
        for result in all_results:
            key = (result['start'], result['end'], result['type'])
            if key not in seen:
                seen.add(key)
                unique_results.append(result)
        
        # Sort by start position
        unique_results.sort(key=lambda x: x['start'])
        
        return unique_results
    
    @staticmethod
    def _luhn_check(card_number: str) -> bool:
        """
        Validate credit card number using Luhn algorithm.
        
        Args:
            card_number: Credit card number as string
            
        Returns:
            True if valid according to Luhn algorithm, False otherwise
        """
        def digits_of(n):
            return [int(d) for d in str(n)]
        
        digits = digits_of(card_number)
        odd_digits = digits[-1::-2]
        even_digits = digits[-2::-2]
        checksum = sum(odd_digits)
        for d in even_digits:
            checksum += sum(digits_of(d * 2))
        return checksum % 10 == 0


# Example usage
if __name__ == "__main__":
    phi_detector = Patterns()
    
    sample_text = """
    Patient: John Doe
    SIN: 123-456-789
    PHN: 9876543210
    Phone: (604) 555-1234
    Email: john.doe@example.com
    Address: 123 Main St, Vancouver, BC V6B 1A1
    MRN: P-123456
    Date of Birth: 01/15/1980
    Care Card: BC1234567890
    """
    
    print("Detecting PHI in sample text...\n")
    results = phi_detector.detect_all(sample_text)
    
    for result in results:
        print(f"Type: {result['type']}")
        print(f"Value: {result['value']}")
        print(f"Position: {result['start']}-{result['end']}")
        print(f"Confidence: {result['confidence']:.2f}")
        print(f"HIPAA Identifier: {result['hipaa_identifier']}")
        print("-" * 50)