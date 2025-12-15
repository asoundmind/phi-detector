#!/usr/bin/env python3
"""
Test script for Chain of Thought enhancements in PHI Detector.
"""

import sys
from src.chain_of_thought import (
    ReasoningChain,
    ClassificationReasoning,
    RiskAssessmentReasoning
)

def test_classification_reasoning():
    """Test classification reasoning chains."""
    print("="*80)
    print("TEST 1: Classification Reasoning")
    print("="*80)

    # Test PII pattern detection
    patterns = {
        'Email': True,
        'Phone': True,
        'SSN': False,
        'Account Number': False,
        'Date of Birth': False
    }

    pii_chain = ClassificationReasoning.analyze_pii_patterns(
        "User test@test.com with phone 555-1234",
        patterns
    )
    print(pii_chain.format())

    # Test dev ticket detection
    print("\n" + "="*80)
    print("TEST 2: Development Ticket Classification")
    print("="*80)

    indicators = ['encryption', 'storing', 'compliance', 'chat message']
    dev_chain = ClassificationReasoning.analyze_dev_indicators(
        "As a PM, I'm building a chat messaging system. Does it need encryption?",
        indicators,
        has_questions=True
    )
    print(dev_chain.format())


def test_risk_assessment():
    """Test risk assessment reasoning."""
    print("\n" + "="*80)
    print("TEST 3: Risk Assessment Reasoning")
    print("="*80)

    detections = [
        {'type': 'SSN', 'value': '123-45-6789'},
        {'type': 'EMAIL', 'value': 'test@test.com'},
        {'type': 'PHONE_NUMBER', 'value': '555-1234'},
        {'type': 'PERSON_NAME', 'value': 'John Doe'}
    ]

    critical_types = {'SSN', 'MEDICAL_RECORD_NUMBER', 'HEALTH_PLAN_NUMBER'}
    high_risk_types = {'CREDIT_CARD', 'BANK_ACCOUNT', 'DATE_OF_BIRTH'}
    medium_risk_types = {'EMAIL', 'PHONE_NUMBER', 'PERSON_NAME'}

    risk_chain = RiskAssessmentReasoning.assess_risk(
        detections,
        critical_types,
        high_risk_types,
        medium_risk_types
    )
    print(risk_chain.format())


def test_custom_reasoning_chain():
    """Test creating custom reasoning chains."""
    print("\n" + "="*80)
    print("TEST 4: Custom Reasoning Chain")
    print("="*80)

    chain = ReasoningChain("Policy Interpretation")

    chain.add_step(
        "Identifying applicable regulations",
        [
            "Message mentions 'healthcare' → PHIPA may apply",
            "Message mentions 'patient' → Medical context confirmed",
            "Ontario jurisdiction → Ontario PHIPA takes precedence"
        ],
        "PHIPA (Ontario) is the primary regulation"
    )

    chain.add_step(
        "Analyzing data classification",
        [
            "Patient health records = Personal Health Information (PHI)",
            "PHI is most sensitive category under PHIPA",
            "Requires highest level of protection"
        ],
        "Data classified as PHI - CRITICAL sensitivity"
    )

    chain.add_step(
        "Determining compliance requirements",
        [
            "PHIPA Section 12: Technical safeguards required",
            "PHIPA Section 13: Administrative safeguards required",
            "PHIPA Section 14: Physical safeguards required"
        ],
        "Comprehensive safeguards mandated across all domains"
    )

    chain.set_conclusion(
        "Healthcare patient records require PHIPA compliance with technical, administrative, and physical safeguards",
        "HIGH"
    )

    print(chain.format())

    # Test JSON serialization
    print("\n" + "-"*80)
    print("JSON Representation:")
    print("-"*80)
    import json
    print(json.dumps(chain.to_dict(), indent=2))


def main():
    """Run all CoT tests."""
    print("\n" + "="*80)
    print(" Chain of Thought (CoT) Enhancement Tests")
    print("="*80)
    print()

    try:
        test_classification_reasoning()
        test_risk_assessment()
        test_custom_reasoning_chain()

        print("\n" + "="*80)
        print("✅ All CoT tests completed successfully!")
        print("="*80)
        print()
        print("Next steps:")
        print("1. Start the Streamlit app: streamlit run app.py")
        print("2. Test with different message types to see CoT reasoning in action")
        print("3. Check the expandable 'Reasoning' sections in the UI")
        print()

    except Exception as e:
        print(f"\n❌ Error during testing: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
