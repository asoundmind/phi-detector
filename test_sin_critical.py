#!/usr/bin/env python3
"""
Test to verify that SIN (Social Insurance Number) is classified as CRITICAL risk.
"""

from src.chatbot import ChatBot

def test_sin_critical_risk():
    """Test that SIN is properly classified as CRITICAL risk."""
    print("="*80)
    print("Testing SIN Classification as CRITICAL Risk")
    print("="*80)

    # Initialize chatbot
    print("\nInitializing ChatBot...")
    chatbot = ChatBot()

    # Test ticket with SIN
    test_ticket = """
    Support Ticket #45678
    Customer: Jane Smith
    Email: jane.smith@example.com
    SIN: 123-456-789
    Issue: Need to update personal information
    """

    print("\nTest Ticket:")
    print(test_ticket)
    print("\n" + "-"*80)

    # Analyze the ticket
    print("\nAnalyzing ticket...")
    response, prompt, detections, risk_level, context_chunks, risk_reasoning = chatbot.analyze_ticket(
        test_ticket,
        return_prompt=True,
        use_cot=True
    )

    print(f"\n{'='*80}")
    print("RESULTS")
    print("="*80)

    print(f"\nDetected PII Types:")
    for det in detections:
        print(f"  - {det['type']}: {det['value']}")

    print(f"\n{'='*80}")
    print(f"RISK LEVEL: {risk_level}")
    print("="*80)

    if risk_level == "CRITICAL":
        print("\n✅ SUCCESS: SIN properly classified as CRITICAL risk!")
    else:
        print(f"\n❌ FAILURE: SIN classified as {risk_level} instead of CRITICAL!")

    # Display reasoning chain if available
    if risk_reasoning:
        print("\n" + "="*80)
        print("Risk Assessment Reasoning:")
        print("="*80)
        print(risk_reasoning.format(include_header=False))

    return risk_level == "CRITICAL"


if __name__ == "__main__":
    success = test_sin_critical_risk()
    exit(0 if success else 1)
