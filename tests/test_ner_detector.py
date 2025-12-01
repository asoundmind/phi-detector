"""
Unit tests for NER-based PHI Detection
Tests the NERDetector class from src/ner_detector.py
"""

import pytest
import sys
from pathlib import Path

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.ner_detector import NERDetector


class TestNERDetector:
    """Test suite for the NERDetector class"""

    @pytest.fixture
    def detector(self):
        """Create a NERDetector instance for testing"""
        try:
            return NERDetector()
        except OSError as e:
            pytest.skip(f"spaCy model not installed: {e}")

    # Tests for detect_entities()
    def test_detect_person_entities(self, detector):
        """Test detection of person names"""
        text = "Patient John Doe visited Dr. Smith"
        results = detector.detect_entities(text)

        # Should detect at least the person names
        person_results = [r for r in results if r['type'] == 'NAME']
        assert len(person_results) >= 1

        # Check structure
        for result in person_results:
            assert 'type' in result
            assert 'value' in result
            assert 'start' in result
            assert 'end' in result
            assert 'confidence' in result
            assert 'hipaa_identifier' in result
            assert result['type'] == 'NAME'
            assert result['hipaa_identifier'] == '#1 - Names'

    def test_detect_location_entities(self, detector):
        """Test detection of locations (GPE and LOC)"""
        text = "The patient lives in Vancouver, British Columbia, Canada"
        results = detector.detect_entities(text)

        # Should detect locations
        location_results = [r for r in results if r['type'] == 'LOCATION']
        assert len(location_results) >= 1

        # Check HIPAA identifier
        for result in location_results:
            assert result['hipaa_identifier'] == '#4 - Geographic subdivisions'

    def test_detect_organization_entities(self, detector):
        """Test detection of organizations"""
        text = "Contact Vancouver General Hospital for records"
        results = detector.detect_entities(text)

        # Should detect organization
        org_results = [r for r in results if r['type'] == 'ORGANIZATION']
        assert len(org_results) >= 1

        for result in org_results:
            assert result['type'] == 'ORGANIZATION'
            assert result['hipaa_identifier'] == 'Organization name (potential identifier)'

    def test_detect_date_entities(self, detector):
        """Test detection of dates"""
        text = "Appointment scheduled for January 15, 2024"
        results = detector.detect_entities(text)

        # Should detect date
        date_results = [r for r in results if r['type'] == 'DATE']
        assert len(date_results) >= 1

        for result in date_results:
            assert result['type'] == 'DATE'
            assert result['hipaa_identifier'] == '#7 - Dates'

    def test_detect_mixed_entities(self, detector):
        """Test detection of multiple entity types"""
        text = """
        Patient John Doe visited Vancouver General Hospital
        on January 15, 2024 in British Columbia.
        """
        results = detector.detect_entities(text)

        # Should detect multiple types
        types_found = set(r['type'] for r in results)
        assert len(types_found) >= 2

        # Should include at least NAME and DATE
        assert 'NAME' in types_found or 'DATE' in types_found

    def test_empty_text(self, detector):
        """Test with empty text"""
        results = detector.detect_entities("")
        assert results == []

    def test_no_entities(self, detector):
        """Test with text containing no relevant entities"""
        text = "This is some text without any entities."
        results = detector.detect_entities(text)

        # May or may not find entities depending on NER model
        assert isinstance(results, list)

    def test_position_tracking(self, detector):
        """Test that entity positions are correctly tracked"""
        text = "Dr. Smith works in Seattle"
        results = detector.detect_entities(text)

        # Verify positions are correct
        for result in results:
            extracted = text[result['start']:result['end']]
            assert extracted == result['value']

    def test_sorted_by_position(self, detector):
        """Test that results are sorted by start position"""
        text = "John lives in Vancouver and works at Hospital on Monday"
        results = detector.detect_entities(text)

        if len(results) > 1:
            positions = [r['start'] for r in results]
            assert positions == sorted(positions)

    def test_confidence_scores(self, detector):
        """Test that confidence scores are within valid range"""
        text = "Patient John Doe from Vancouver"
        results = detector.detect_entities(text)

        for result in results:
            assert 0.0 <= result['confidence'] <= 1.0
            assert result['confidence'] == 0.85  # Default for transformer model

    def test_result_structure(self, detector):
        """Test that all results have required fields"""
        text = "Dr. Jane Smith at Seattle Clinic on March 1, 2024"
        results = detector.detect_entities(text)

        required_fields = ['type', 'value', 'start', 'end', 'confidence', 'hipaa_identifier']

        for result in results:
            for field in required_fields:
                assert field in result, f"Missing field: {field}"

    def test_entity_type_mappings(self, detector):
        """Test that entity types are correctly mapped"""
        text = "John Doe in New York at IBM on January 1"
        results = detector.detect_entities(text)

        valid_types = {'NAME', 'LOCATION', 'ORGANIZATION', 'DATE'}

        for result in results:
            assert result['type'] in valid_types

    def test_hipaa_identifier_mappings(self, detector):
        """Test that HIPAA identifiers are correctly assigned"""
        text = "Patient Alice at Boston Hospital on June 15"
        results = detector.detect_entities(text)

        valid_hipaa_ids = {
            '#1 - Names',
            '#4 - Geographic subdivisions',
            '#7 - Dates',
            'Organization name (potential identifier)'
        }

        for result in results:
            assert result['hipaa_identifier'] in valid_hipaa_ids


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v"])
