#!/usr/bin/env python3
"""
Simple unit test for risk classification of Canadian critical identifiers.
"""

from src.chatbot import ChatBot

def test_risk_classification():
    """Test risk level classification for different PHI types."""
    print("="*80)
    print("Unit Test: Risk Level Classification")
    print("="*80)

    chatbot = ChatBot()

    # Test cases: (description, detections, expected_risk)
    test_cases = [
        (
            "SIN only",
            [{'type': 'Social Insurance Number (SIN)', 'value': '123-456-789'}],
            "CRITICAL"
        ),
        (
            "PHN only",
            [{'type': 'Personal Health Number (PHN)', 'value': '1234567890'}],
            "CRITICAL"
        ),
        (
            "Credit Card only",
            [{'type': 'Credit Card Number', 'value': '4532-1488-0343-6467'}],
            "CRITICAL"
        ),
        (
            "SSN only",
            [{'type': 'SSN', 'value': '123-45-6789'}],
            "CRITICAL"
        ),
        (
            "Email only",
            [{'type': 'Email Address', 'value': 'test@test.com'}],
            "MEDIUM"
        ),
        (
            "Phone only",
            [{'type': 'Phone Number', 'value': '604-555-1234'}],
            "MEDIUM"
        ),
        (
            "SIN + Email",
            [
                {'type': 'Social Insurance Number (SIN)', 'value': '123-456-789'},
                {'type': 'Email Address', 'value': 'test@test.com'}
            ],
            "CRITICAL"
        ),
        (
            "Multiple emails (no critical)",
            [
                {'type': 'Email Address', 'value': 'test1@test.com'},
                {'type': 'Email Address', 'value': 'test2@test.com'},
                {'type': 'Phone Number', 'value': '604-555-1234'},
            ],
            "MEDIUM"
        ),
    ]

    results = []
    for description, detections, expected in test_cases:
        actual = chatbot._assess_risk_level(detections)
        passed = actual == expected
        results.append((description, expected, actual, passed))

        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"\n{status} | {description}")
        print(f"   Expected: {expected}, Got: {actual}")
        if detections:
            print(f"   Types: {[d['type'] for d in detections]}")

    # Summary
    print("\n" + "="*80)
    print("SUMMARY")
    print("="*80)

    passed_count = sum(1 for _, _, _, passed in results if passed)
    total_count = len(results)

    print(f"\nPassed: {passed_count}/{total_count}")

    if passed_count == total_count:
        print("\n✅ ALL TESTS PASSED!")
        print("\nKey findings:")
        print("  • SIN (Social Insurance Number) → CRITICAL ✅")
        print("  • PHN (Personal Health Number) → CRITICAL ✅")
        print("  • Credit Card Number → CRITICAL ✅")
        print("  • SSN → CRITICAL ✅")
    else:
        print("\n❌ SOME TESTS FAILED")
        for desc, exp, act, passed in results:
            if not passed:
                print(f"  • {desc}: expected {exp}, got {act}")

    return passed_count == total_count


if __name__ == "__main__":
    success = test_risk_classification()
    exit(0 if success else 1)
