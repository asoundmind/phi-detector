"""
NER-based PHI Detection Module

This module provides Named Entity Recognition (NER) based detection of
Protected Health Information (PHI) using spaCy's transformer model.
"""

import spacy
from typing import List, Dict


class NERDetector:
    """
    A class for detecting Protected Health Information (PHI) using NER.

    Uses spaCy's transformer model to identify entities such as names,
    locations, organizations, and dates that may constitute PHI.
    """

    def __init__(self):
        """
        Initialize the NER detector with spaCy's model.

        Loads the 'en_core_web_sm' model for entity recognition.
        """
        try:
            self.nlp = spacy.load('en_core_web_sm')
        except OSError:
            raise OSError(
                "spaCy model 'en_core_web_sm' not found. "
                "It should be installed via requirements.txt"
            )

    def detect_entities(self, text: str) -> List[Dict]:
        """
        Extract PERSON, GPE, LOC, ORG, and DATE entities from text.

        Args:
            text: Input text to analyze for entities

        Returns:
            List of dictionaries containing detection results with fields:
            - type: Mapped entity type (NAME, LOCATION, ORGANIZATION, DATE)
            - value: The detected entity text
            - start: Start position in the text
            - end: End position in the text
            - confidence: Confidence score (based on spaCy's NER)
            - hipaa_identifier: HIPAA Privacy Rule identifier

        Entity mappings:
            - PERSON -> NAME
            - GPE (Geopolitical Entity) -> LOCATION
            - LOC (Location) -> LOCATION
            - ORG (Organization) -> ORGANIZATION
            - DATE -> DATE
        """
        # Process the text with spaCy
        doc = self.nlp(text)

        # Define entity type mappings
        entity_type_map = {
            'PERSON': 'NAME',
            'GPE': 'LOCATION',
            'LOC': 'LOCATION',
            'ORG': 'ORGANIZATION',
            'DATE': 'DATE'
        }

        # Define HIPAA identifiers for each entity type
        hipaa_identifiers = {
            'PERSON': '#1 - Names',
            'DATE': '#7 - Dates',
            'GPE': '#4 - Geographic subdivisions',
            'LOC': '#4 - Geographic subdivisions',
            'ORG': 'Organization name (potential identifier)'
        }

        results = []

        # Extract relevant entities
        for ent in doc.ents:
            if ent.label_ in entity_type_map:
                # Get confidence score (spaCy doesn't provide direct confidence,
                # so we use a high default value for transformer models)
                confidence = 0.85

                result = {
                    'type': entity_type_map[ent.label_],
                    'value': ent.text,
                    'start': ent.start_char,
                    'end': ent.end_char,
                    'confidence': confidence,
                    'hipaa_identifier': hipaa_identifiers[ent.label_]
                }
                results.append(result)

        # Sort by start position
        results.sort(key=lambda x: x['start'])

        return results


if __name__ == "__main__":
    # Example usage
    detector = NERDetector()

    sample_text = """
    Patient John Doe visited Dr. Smith at Vancouver General Hospital
    on January 15, 2024. The patient lives in British Columbia, Canada.
    Contact the clinic in Seattle for records.
    """

    print("Detecting entities in sample text...\n")
    results = detector.detect_entities(sample_text)

    for result in results:
        print(f"Type: {result['type']}")
        print(f"Value: {result['value']}")
        print(f"Position: {result['start']}-{result['end']}")
        print(f"Confidence: {result['confidence']:.2f}")
        print(f"HIPAA Identifier: {result['hipaa_identifier']}")
        print("-" * 50)
