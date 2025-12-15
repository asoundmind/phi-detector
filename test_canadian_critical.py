#!/usr/bin/env python3
"""
Test to verify that Canadian critical identifiers (SIN, PHN) are classified as CRITICAL risk.
"""

from src.chatbot import ChatBot

def test_canadian_critical_identifiers():
    """Test that SIN and PHN are properly classified as CRITICAL risk."""
    print("="*80)
    print("Testing Canadian Critical Identifiers (SIN & PHN)")
    print("="*80)

    # Initialize chatbot
    print("\nInitializing ChatBot...")
    chatbot = ChatBot()

    # Test 1: SIN only
    print("\n" + "="*80)
    print("TEST 1: SIN (Social Insurance Number)")
    print("="*80)

    ticket1 = "Customer needs help. SIN: 987-654-321, Email: test@test.com"
    print(f"\nTicket: {ticket1}")

    _, _, detections1, risk1, _, _ = chatbot.analyze_ticket(ticket1, return_prompt=True, use_cot=True)

    print(f"\nDetected: {[d['type'] for d in detections1]}")
    print(f"Risk Level: {risk1}")
    print(f"✅ PASS" if risk1 == "CRITICAL" else f"❌ FAIL - Expected CRITICAL, got {risk1}")

    # Test 2: PHN only
    print("\n" + "="*80)
    print("TEST 2: PHN (Personal Health Number)")
    print("="*80)

    ticket2 = "Patient PHN: 1234567890, needs appointment"
    print(f"\nTicket: {ticket2}")

    _, _, detections2, risk2, _, _ = chatbot.analyze_ticket(ticket2, return_prompt=True, use_cot=True)

    print(f"\nDetected: {[d['type'] for d in detections2]}")
    print(f"Risk Level: {risk2}")
    print(f"✅ PASS" if risk2 == "CRITICAL" else f"❌ FAIL - Expected CRITICAL, got {risk2}")

    # Test 3: Both SIN and PHN
    print("\n" + "="*80)
    print("TEST 3: Both SIN and PHN")
    print("="*80)

    ticket3 = "Patient data - SIN: 123-456-789, PHN: 9876543210"
    print(f"\nTicket: {ticket3}")

    _, _, detections3, risk3, _, _ = chatbot.analyze_ticket(ticket3, return_prompt=True, use_cot=True)

    print(f"\nDetected: {[d['type'] for d in detections3]}")
    print(f"Risk Level: {risk3}")
    print(f"✅ PASS" if risk3 == "CRITICAL" else f"❌ FAIL - Expected CRITICAL, got {risk3}")

    # Test 4: Credit Card (also should be CRITICAL now)
    print("\n" + "="*80)
    print("TEST 4: Credit Card")
    print("="*80)

    ticket4 = "Payment issue. Card: 4532-1488-0343-6467"
    print(f"\nTicket: {ticket4}")

    _, _, detections4, risk4, _, _ = chatbot.analyze_ticket(ticket4, return_prompt=True, use_cot=True)

    print(f"\nDetected: {[d['type'] for d in detections4]}")
    print(f"Risk Level: {risk4}")
    print(f"✅ PASS" if risk4 == "CRITICAL" else f"❌ FAIL - Expected CRITICAL, got {risk4}")

    # Summary
    print("\n" + "="*80)
    print("SUMMARY")
    print("="*80)

    all_pass = all([risk1 == "CRITICAL", risk2 == "CRITICAL", risk3 == "CRITICAL", risk4 == "CRITICAL"])

    if all_pass:
        print("\n✅ ALL TESTS PASSED - Canadian critical identifiers properly classified!")
    else:
        print("\n❌ SOME TESTS FAILED")

    return all_pass


if __name__ == "__main__":
    success = test_canadian_critical_identifiers()
    exit(0 if success else 1)
