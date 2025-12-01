"""
PHI Detector - Combined Pattern and NER Detection

This module provides a comprehensive PHI detection system that combines
regex-based pattern matching with NER-based entity detection.
"""

from typing import List, Dict
from .patterns import Patterns
from .ner_detector import NERDetector


class PHIDetector:
    """
    Comprehensive PHI detector combining pattern matching and NER.

    This class integrates both regex-based pattern detection and
    Named Entity Recognition to identify Protected Health Information.
    """

    def __init__(self):
        """
        Initialize the PHI detector with both detection engines.

        Initializes:
        - Patterns: Regex-based detector for structured PHI (SSN, phone, etc.)
        - NERDetector: spaCy-based detector for names, locations, dates, etc.
        """
        self.patterns = Patterns()
        self.ner_detector = NERDetector()

    def analyze(self, text: str) -> Dict:
        """
        Analyze text for PHI using both pattern matching and NER.

        Args:
            text: Input text to analyze

        Returns:
            Dictionary containing:
            - has_phi (bool): Whether PHI was detected
            - risk_level (str): 'HIGH', 'MEDIUM', or 'LOW'
            - detections (list): List of all detected PHI items
            - redacted_text (str): Text with PHI replaced by [TYPE] placeholders

        Risk levels:
        - HIGH: SSN or Credit Card detected
        - MEDIUM: 3 or more PHI items detected
        - LOW: 1-2 PHI items detected
        """
        # Run both detection methods
        pattern_results = self.patterns.detect_all(text)
        ner_results = self.ner_detector.detect_entities(text)

        # Merge and remove overlaps
        merged_detections = self._merge_detections(pattern_results, ner_results)

        # Calculate risk level
        risk_level = self._calculate_risk(merged_detections)

        # Redact text
        redacted_text = self._redact_text(text, merged_detections)

        return {
            'has_phi': len(merged_detections) > 0,
            'risk_level': risk_level,
            'detections': merged_detections,
            'redacted_text': redacted_text
        }

    def _merge_detections(self, pattern_results: List[Dict], ner_results: List[Dict]) -> List[Dict]:
        """
        Merge pattern and NER results, removing overlapping detections.

        When detections overlap, pattern-based results take precedence
        as they are more specific (e.g., SSN pattern vs. generic number).

        Args:
            pattern_results: Results from pattern-based detection
            ner_results: Results from NER-based detection

        Returns:
            Merged list of detections with overlaps removed
        """
        # Start with all pattern results (they have higher priority)
        merged = list(pattern_results)

        # Add NER results that don't overlap with pattern results
        for ner_item in ner_results:
            ner_start = ner_item['start']
            ner_end = ner_item['end']

            # Check if this NER result overlaps with any pattern result
            overlaps = False
            for pattern_item in pattern_results:
                pattern_start = pattern_item['start']
                pattern_end = pattern_item['end']

                # Check for overlap
                if not (ner_end <= pattern_start or ner_start >= pattern_end):
                    overlaps = True
                    break

            # Add if no overlap found
            if not overlaps:
                merged.append(ner_item)

        # Sort by start position
        merged.sort(key=lambda x: x['start'])

        return merged

    def _calculate_risk(self, detections: List[Dict]) -> str:
        """
        Calculate risk level based on detected PHI.

        Args:
            detections: List of detected PHI items

        Returns:
            Risk level: 'HIGH', 'MEDIUM', or 'LOW'
        """
        if not detections:
            return 'LOW'

        # Check for high-risk PHI types
        high_risk_types = {
            'Social Insurance Number (SIN)',
            'Credit Card Number',
            'SSN',
            'CreditCard',
            'Personal Health Number (PHN)'
        }

        for detection in detections:
            if detection['type'] in high_risk_types:
                return 'HIGH'

        # Check count for medium risk
        if len(detections) >= 3:
            return 'MEDIUM'

        return 'LOW'

    def _redact_text(self, text: str, detections: List[Dict]) -> str:
        """
        Redact PHI from text by replacing with [TYPE] placeholders.

        Args:
            text: Original text
            detections: List of detected PHI items

        Returns:
            Redacted text with PHI replaced by placeholders
        """
        if not detections:
            return text

        # Sort detections by start position in reverse order
        # (process from end to start to preserve positions)
        sorted_detections = sorted(detections, key=lambda x: x['start'], reverse=True)

        # Convert text to list for easier manipulation
        redacted = text

        for detection in sorted_detections:
            start = detection['start']
            end = detection['end']
            phi_type = detection['type'].upper().replace(' ', '_')

            # Create placeholder
            placeholder = f"[{phi_type}]"

            # Replace the PHI with placeholder
            redacted = redacted[:start] + placeholder + redacted[end:]

        return redacted


if __name__ == "__main__":
    # Example usage
    detector = PHIDetector()

    sample_text = """
    Patient John Doe, SIN: 123-456-789, called from (604) 555-1234.
    Email: john.doe@example.com
    Address: 123 Main St, Vancouver, BC V6B 1A1
    Appointment: 2024-01-15
    """

    print("Analyzing text for PHI...\n")
    results = detector.analyze(sample_text)

    print(f"PHI Detected: {results['has_phi']}")
    print(f"Risk Level: {results['risk_level']}")
    print(f"\nDetections ({len(results['detections'])}):")
    for detection in results['detections']:
        print(f"  - {detection['type']}: {detection['value']} "
              f"(confidence: {detection['confidence']:.2f})")

    print(f"\nRedacted Text:")
    print(results['redacted_text'])
