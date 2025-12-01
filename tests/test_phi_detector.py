"""
Unit tests for PHIDetector
Tests the PHIDetector class from src/phi_detector.py
"""

import pytest
import sys
from pathlib import Path

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.phi_detector import PHIDetector


class TestPHIDetector:
    """Test suite for the PHIDetector class"""

    @pytest.fixture
    def detector(self):
        """Create a PHIDetector instance for testing"""
        try:
            return PHIDetector()
        except OSError as e:
            pytest.skip(f"spaCy model not installed: {e}")

    # Tests for analyze()
    def test_analyze_with_high_risk_sin(self, detector):
        """Test analysis with SIN (high risk)"""
        text = "Patient SIN: 123-456-789"
        result = detector.analyze(text)

        assert result['has_phi'] == True
        assert result['risk_level'] == 'HIGH'
        assert len(result['detections']) >= 1
        assert isinstance(result['redacted_text'], str)

    def test_analyze_with_high_risk_credit_card(self, detector):
        """Test analysis with credit card (high risk)"""
        text = "Card: 4532015112830366"
        result = detector.analyze(text)

        assert result['has_phi'] == True
        assert result['risk_level'] == 'HIGH'

    def test_analyze_with_medium_risk(self, detector):
        """Test analysis with 3+ items (medium risk)"""
        text = "Email: test@example.com, Phone: 604-555-1234, IP: 192.168.1.1"
        result = detector.analyze(text)

        assert result['has_phi'] == True
        if len(result['detections']) >= 3:
            assert result['risk_level'] == 'MEDIUM'

    def test_analyze_with_low_risk(self, detector):
        """Test analysis with 1-2 items (low risk)"""
        text = "Email: test@example.com"
        result = detector.analyze(text)

        assert result['has_phi'] == True
        # Could be LOW or MEDIUM depending on NER detection
        assert result['risk_level'] in ['LOW', 'MEDIUM']

    def test_analyze_no_phi(self, detector):
        """Test analysis with no PHI"""
        text = "This is a normal sentence without any sensitive data"
        result = detector.analyze(text)

        assert result['has_phi'] == False
        assert result['risk_level'] == 'LOW'
        assert len(result['detections']) == 0
        assert result['redacted_text'] == text

    def test_analyze_result_structure(self, detector):
        """Test that analyze returns correct structure"""
        text = "Test text"
        result = detector.analyze(text)

        assert 'has_phi' in result
        assert 'risk_level' in result
        assert 'detections' in result
        assert 'redacted_text' in result

        assert isinstance(result['has_phi'], bool)
        assert isinstance(result['risk_level'], str)
        assert isinstance(result['detections'], list)
        assert isinstance(result['redacted_text'], str)

    def test_analyze_risk_levels(self, detector):
        """Test that risk levels are valid"""
        text = "Email: test@example.com"
        result = detector.analyze(text)

        assert result['risk_level'] in ['HIGH', 'MEDIUM', 'LOW']

    # Tests for _merge_detections()
    def test_merge_detections_no_overlap(self, detector):
        """Test merging detections with no overlap"""
        pattern_results = [
            {'type': 'Email', 'start': 0, 'end': 10, 'value': 'test@x.com'}
        ]
        ner_results = [
            {'type': 'NAME', 'start': 20, 'end': 30, 'value': 'John Doe'}
        ]

        merged = detector._merge_detections(pattern_results, ner_results)

        assert len(merged) == 2

    def test_merge_detections_with_overlap(self, detector):
        """Test that overlapping detections are removed"""
        pattern_results = [
            {'type': 'Phone', 'start': 10, 'end': 22, 'value': '604-555-1234'}
        ]
        ner_results = [
            {'type': 'DATE', 'start': 15, 'end': 25, 'value': '555-1234'}
        ]

        merged = detector._merge_detections(pattern_results, ner_results)

        # Should only keep pattern result (higher priority)
        assert len(merged) == 1
        assert merged[0]['type'] == 'Phone'

    def test_merge_detections_sorted(self, detector):
        """Test that merged detections are sorted by position"""
        pattern_results = [
            {'type': 'Email', 'start': 20, 'end': 30}
        ]
        ner_results = [
            {'type': 'NAME', 'start': 5, 'end': 15}
        ]

        merged = detector._merge_detections(pattern_results, ner_results)

        positions = [d['start'] for d in merged]
        assert positions == sorted(positions)

    def test_merge_detections_empty(self, detector):
        """Test merging with empty lists"""
        merged = detector._merge_detections([], [])
        assert merged == []

    # Tests for _calculate_risk()
    def test_calculate_risk_high_sin(self, detector):
        """Test high risk calculation with SIN"""
        detections = [
            {'type': 'Social Insurance Number (SIN)', 'value': '123-456-789'}
        ]
        risk = detector._calculate_risk(detections)
        assert risk == 'HIGH'

    def test_calculate_risk_high_credit_card(self, detector):
        """Test high risk calculation with credit card"""
        detections = [
            {'type': 'Credit Card Number', 'value': '4532015112830366'}
        ]
        risk = detector._calculate_risk(detections)
        assert risk == 'HIGH'

    def test_calculate_risk_high_phn(self, detector):
        """Test high risk calculation with PHN"""
        detections = [
            {'type': 'Personal Health Number (PHN)', 'value': '1234567890'}
        ]
        risk = detector._calculate_risk(detections)
        assert risk == 'HIGH'

    def test_calculate_risk_medium(self, detector):
        """Test medium risk calculation with 3+ items"""
        detections = [
            {'type': 'Email', 'value': 'test@example.com'},
            {'type': 'Phone', 'value': '604-555-1234'},
            {'type': 'IP', 'value': '192.168.1.1'}
        ]
        risk = detector._calculate_risk(detections)
        assert risk == 'MEDIUM'

    def test_calculate_risk_low_single(self, detector):
        """Test low risk calculation with single item"""
        detections = [
            {'type': 'Email', 'value': 'test@example.com'}
        ]
        risk = detector._calculate_risk(detections)
        assert risk == 'LOW'

    def test_calculate_risk_low_two_items(self, detector):
        """Test low risk calculation with two items"""
        detections = [
            {'type': 'Email', 'value': 'test@example.com'},
            {'type': 'Phone', 'value': '604-555-1234'}
        ]
        risk = detector._calculate_risk(detections)
        assert risk == 'LOW'

    def test_calculate_risk_empty(self, detector):
        """Test risk calculation with no detections"""
        risk = detector._calculate_risk([])
        assert risk == 'LOW'

    # Tests for _redact_text()
    def test_redact_text_single_item(self, detector):
        """Test redacting text with single detection"""
        text = "Email: test@example.com"
        detections = [
            {'type': 'Email Address', 'start': 7, 'end': 23, 'value': 'test@example.com'}
        ]

        redacted = detector._redact_text(text, detections)

        assert '[EMAIL_ADDRESS]' in redacted
        assert 'test@example.com' not in redacted

    def test_redact_text_multiple_items(self, detector):
        """Test redacting text with multiple detections"""
        text = "Email: test@x.com, Phone: 604-555-1234"
        detections = [
            {'type': 'Email Address', 'start': 7, 'end': 17, 'value': 'test@x.com'},
            {'type': 'Phone Number', 'start': 26, 'end': 38, 'value': '604-555-1234'}
        ]

        redacted = detector._redact_text(text, detections)

        assert '[EMAIL_ADDRESS]' in redacted
        assert '[PHONE_NUMBER]' in redacted
        assert 'test@x.com' not in redacted
        assert '604-555-1234' not in redacted

    def test_redact_text_preserves_structure(self, detector):
        """Test that redaction preserves text structure"""
        text = "Start test@example.com End"
        detections = [
            {'type': 'Email', 'start': 6, 'end': 22, 'value': 'test@example.com'}
        ]

        redacted = detector._redact_text(text, detections)

        assert redacted.startswith('Start')
        assert redacted.endswith('End')

    def test_redact_text_empty_detections(self, detector):
        """Test redacting text with no detections"""
        text = "No sensitive data here"
        redacted = detector._redact_text(text, [])

        assert redacted == text

    def test_redact_text_handles_spaces(self, detector):
        """Test that redaction handles types with spaces"""
        text = "SIN: 123-456-789"
        detections = [
            {'type': 'Social Insurance Number (SIN)', 'start': 5, 'end': 16, 'value': '123-456-789'}
        ]

        redacted = detector._redact_text(text, detections)

        assert '[SOCIAL_INSURANCE_NUMBER_(SIN)]' in redacted

    # Integration tests
    def test_end_to_end_comprehensive(self, detector):
        """Test complete workflow with various PHI types"""
        text = """
        Patient: John Doe
        SIN: 123-456-789
        Email: john.doe@example.com
        Phone: 604-555-1234
        Address: Vancouver, BC V6B 1A1
        Date: 2024-01-15
        """

        result = detector.analyze(text)

        assert result['has_phi'] == True
        assert result['risk_level'] == 'HIGH'  # Due to SIN
        assert len(result['detections']) >= 3
        assert 'john.doe@example.com' not in result['redacted_text']

    def test_end_to_end_pattern_only(self, detector):
        """Test with only pattern-based PHI"""
        text = "Contact: test@example.com or 604-555-1234"

        result = detector.analyze(text)

        assert result['has_phi'] == True
        assert len(result['detections']) >= 2

    def test_end_to_end_empty(self, detector):
        """Test with empty text"""
        result = detector.analyze("")

        assert result['has_phi'] == False
        assert result['risk_level'] == 'LOW'
        assert result['detections'] == []
        assert result['redacted_text'] == ""


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v"])
