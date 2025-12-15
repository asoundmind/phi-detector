"""
Chain of Thought reasoning utilities for PHI Detector.

This module provides utilities for transparent, step-by-step reasoning
in classification, risk assessment, and compliance analysis.
"""

from typing import List, Dict, Tuple, Optional
import logging

logger = logging.getLogger(__name__)


class ReasoningStep:
    """Represents a single step in chain of thought reasoning."""

    def __init__(self, step_num: int, description: str, findings: List[str], conclusion: str):
        """
        Initialize a reasoning step.

        Args:
            step_num: Step number in the reasoning chain
            description: What this step is analyzing
            findings: List of observations/findings in this step
            conclusion: Conclusion drawn from this step
        """
        self.step_num = step_num
        self.description = description
        self.findings = findings
        self.conclusion = conclusion

    def format(self, indent: int = 0) -> str:
        """Format the reasoning step as a readable string."""
        prefix = "  " * indent
        lines = [f"{prefix}Step {self.step_num}: {self.description}"]

        for finding in self.findings:
            lines.append(f"{prefix}  - {finding}")

        if self.conclusion:
            lines.append(f"{prefix}  → Conclusion: {self.conclusion}")

        return "\n".join(lines)


class ReasoningChain:
    """Manages a chain of thought reasoning process."""

    def __init__(self, title: str):
        """
        Initialize a reasoning chain.

        Args:
            title: Title/description of what this chain is reasoning about
        """
        self.title = title
        self.steps: List[ReasoningStep] = []
        self.final_conclusion: Optional[str] = None
        self.confidence: Optional[str] = None

    def add_step(self, description: str, findings: List[str], conclusion: str) -> 'ReasoningChain':
        """
        Add a reasoning step to the chain.

        Args:
            description: What this step analyzes
            findings: Observations made in this step
            conclusion: Conclusion from this step

        Returns:
            Self for method chaining
        """
        step = ReasoningStep(
            step_num=len(self.steps) + 1,
            description=description,
            findings=findings,
            conclusion=conclusion
        )
        self.steps.append(step)
        return self

    def set_conclusion(self, conclusion: str, confidence: str = None) -> 'ReasoningChain':
        """
        Set the final conclusion of the reasoning chain.

        Args:
            conclusion: Final conclusion
            confidence: Confidence level (e.g., "HIGH", "MEDIUM", "LOW")

        Returns:
            Self for method chaining
        """
        self.final_conclusion = conclusion
        self.confidence = confidence
        return self

    def format(self, include_header: bool = True) -> str:
        """
        Format the entire reasoning chain as a readable string.

        Args:
            include_header: Whether to include the title header

        Returns:
            Formatted reasoning chain
        """
        lines = []

        if include_header:
            lines.append(f"\n{'='*60}")
            lines.append(f"{self.title}")
            lines.append(f"{'='*60}\n")

        for step in self.steps:
            lines.append(step.format())
            lines.append("")  # Blank line between steps

        if self.final_conclusion:
            lines.append(f"Final Conclusion: {self.final_conclusion}")
            if self.confidence:
                lines.append(f"Confidence: {self.confidence}")

        return "\n".join(lines)

    def to_dict(self) -> Dict:
        """
        Convert reasoning chain to dictionary for JSON serialization.

        Returns:
            Dictionary representation
        """
        return {
            'title': self.title,
            'steps': [
                {
                    'step_num': step.step_num,
                    'description': step.description,
                    'findings': step.findings,
                    'conclusion': step.conclusion
                }
                for step in self.steps
            ],
            'final_conclusion': self.final_conclusion,
            'confidence': self.confidence
        }


class ClassificationReasoning:
    """Chain of thought reasoning for message classification."""

    @staticmethod
    def analyze_pii_patterns(message: str, patterns: Dict[str, bool]) -> ReasoningChain:
        """
        Create reasoning chain for PII pattern detection.

        Args:
            message: Message text
            patterns: Dictionary of pattern types and whether they were found

        Returns:
            ReasoningChain with PII analysis
        """
        chain = ReasoningChain("PII Pattern Analysis")

        findings = []
        pii_count = 0

        for pattern_type, found in patterns.items():
            if found:
                findings.append(f"✓ {pattern_type} pattern detected")
                pii_count += 1
            else:
                findings.append(f"✗ {pattern_type} pattern not found")

        findings.append(f"Total PII patterns found: {pii_count}")

        if pii_count >= 2:
            conclusion = f"Contains {pii_count} PII patterns → Likely PII Support Ticket"
        elif pii_count == 1:
            conclusion = "Only 1 PII pattern → Not enough for PII ticket classification"
        else:
            conclusion = "No PII patterns → Not a PII ticket"

        chain.add_step(
            "Scanning for actual PII patterns",
            findings,
            conclusion
        )

        return chain

    @staticmethod
    def analyze_dev_indicators(message: str, indicators: List[str], has_questions: bool) -> ReasoningChain:
        """
        Create reasoning chain for development ticket indicators.

        Args:
            message: Message text
            indicators: List of development indicators found
            has_questions: Whether question words were found

        Returns:
            ReasoningChain with dev ticket analysis
        """
        chain = ReasoningChain("Development Ticket Analysis")

        # Step 1: Development indicators
        if indicators:
            findings = [f"Found: '{ind}'" for ind in indicators]
            findings.append(f"Total: {len(indicators)} development indicators")
            conclusion = f"{len(indicators)} indicators present"
        else:
            findings = ["No development keywords found"]
            conclusion = "Not a development ticket"

        chain.add_step(
            "Checking for development/PM indicators",
            findings,
            conclusion
        )

        # Step 2: Question patterns
        question_findings = []
        if has_questions:
            question_findings.append("✓ Contains question words (should, need, require, what, how)")
            question_conclusion = "Message is asking questions"
        else:
            question_findings.append("✗ No question words found")
            question_conclusion = "Not phrased as questions"

        chain.add_step(
            "Analyzing question patterns",
            question_findings,
            question_conclusion
        )

        # Final determination
        if len(indicators) >= 2 and has_questions:
            chain.set_conclusion(
                "Development/Requirements Ticket",
                "HIGH"
            )
        else:
            chain.set_conclusion(
                "Not a development ticket",
                "HIGH"
            )

        return chain


class RiskAssessmentReasoning:
    """Chain of thought reasoning for risk assessment."""

    @staticmethod
    def assess_risk(detections: List[Dict], critical_types: set, high_risk_types: set, medium_risk_types: set) -> ReasoningChain:
        """
        Create reasoning chain for risk level assessment.

        Args:
            detections: List of PHI detections
            critical_types: Set of critical PHI types
            high_risk_types: Set of high-risk PHI types
            medium_risk_types: Set of medium-risk PHI types

        Returns:
            ReasoningChain with risk assessment
        """
        chain = ReasoningChain("Risk Level Assessment")

        if not detections:
            chain.add_step(
                "Cataloging detected PII",
                ["No PII detected"],
                "No privacy risk"
            )
            chain.set_conclusion("LOW", "HIGH")
            return chain

        # Step 1: Catalog detections
        detected_types = {d['type'] for d in detections}
        catalog_findings = []

        type_counts = {}
        for det in detections:
            det_type = det['type']
            type_counts[det_type] = type_counts.get(det_type, 0) + 1

        for det_type, count in type_counts.items():
            category = "UNKNOWN"
            if det_type in critical_types:
                category = "CRITICAL"
            elif det_type in high_risk_types:
                category = "HIGH"
            elif det_type in medium_risk_types:
                category = "MEDIUM"

            catalog_findings.append(f"{det_type}: {count} instance(s) [{category} category]")

        chain.add_step(
            "Cataloging detected PII types",
            catalog_findings,
            f"Found {len(detections)} PII items across {len(detected_types)} types"
        )

        # Step 2: Identify highest risk elements
        risk_findings = []
        final_risk = "LOW"
        primary_factor = None

        critical_found = detected_types & critical_types
        high_found = detected_types & high_risk_types
        medium_found = detected_types & medium_risk_types

        if critical_found:
            risk_findings.append(f"⚠️ CRITICAL types found: {', '.join(critical_found)}")
            risk_findings.append("Triggers automatic CRITICAL classification")
            final_risk = "CRITICAL"
            primary_factor = f"Presence of {', '.join(critical_found)}"
        elif high_found:
            risk_findings.append(f"⚠️ HIGH-RISK types found: {', '.join(high_found)}")
            final_risk = "HIGH"
            primary_factor = f"Presence of {', '.join(high_found)}"
        elif medium_found:
            risk_findings.append(f"MEDIUM-RISK types found: {', '.join(medium_found)}")
            if len(detections) > 5:
                risk_findings.append(f"Multiple items ({len(detections)}) escalates risk")
                final_risk = "HIGH"
                primary_factor = f"Multiple medium-risk items ({len(detections)} total)"
            else:
                final_risk = "MEDIUM"
                primary_factor = f"Presence of {', '.join(medium_found)}"

        chain.add_step(
            "Identifying highest risk elements",
            risk_findings,
            f"Risk level determined: {final_risk}"
        )

        # Step 3: Context and linkability
        context_findings = []
        if len(detected_types) >= 3:
            context_findings.append(f"Multiple identifier types ({len(detected_types)}) increase linkability risk")
        else:
            context_findings.append(f"Limited identifier types ({len(detected_types)}) reduce linkability")

        chain.add_step(
            "Considering context and linkability",
            context_findings,
            "Context analysis complete"
        )

        # Final conclusion
        secondary_factors = []
        if len(detected_types) >= 3:
            secondary_factors.append("High linkability (multiple identifier types)")

        conclusion_parts = [final_risk]
        if primary_factor:
            conclusion_parts.append(f"\nPrimary Factor: {primary_factor}")
        if secondary_factors:
            conclusion_parts.append(f"Secondary Factors: {', '.join(secondary_factors)}")

        chain.set_conclusion("\n".join(conclusion_parts), "HIGH")

        return chain


class ComplianceReasoning:
    """Chain of thought reasoning for compliance analysis."""

    @staticmethod
    def multi_step_analysis(ticket_text: str, initial_context: List[Tuple], rag_system) -> Tuple[ReasoningChain, List[Tuple]]:
        """
        Perform multi-step RAG analysis with reasoning.

        Args:
            ticket_text: Development ticket text
            initial_context: Initial RAG results
            rag_system: RAG system for additional queries

        Returns:
            Tuple of (ReasoningChain, combined_context)
        """
        chain = ReasoningChain("Multi-Step Compliance Analysis")
        all_context = list(initial_context)

        # Step 1: Initial broad search
        step1_findings = [
            f"Retrieved {len(initial_context)} relevant policy chunks",
        ]

        if initial_context:
            sources = set(metadata.get('source', 'Unknown').split('/')[-1]
                         for _, metadata, _ in initial_context)
            step1_findings.append(f"Sources: {', '.join(sources)}")

        chain.add_step(
            "Initial broad policy search",
            step1_findings,
            f"Found {len(initial_context)} relevant passages"
        )

        # Step 2: Identify gaps and do follow-up
        keywords_to_explore = []
        ticket_lower = ticket_text.lower()

        if 'encryption' in ticket_lower or 'encrypt' in ticket_lower:
            keywords_to_explore.append('encryption standards')
        if 'consent' in ticket_lower:
            keywords_to_explore.append('consent requirements')
        if 'breach' in ticket_lower or 'incident' in ticket_lower:
            keywords_to_explore.append('breach notification')
        if 'retention' in ticket_lower or 'delete' in ticket_lower:
            keywords_to_explore.append('data retention requirements')

        if keywords_to_explore:
            gap_findings = [f"Identified specific topics to explore: {', '.join(keywords_to_explore)}"]

            for keyword in keywords_to_explore[:2]:  # Limit to 2 follow-ups
                try:
                    followup_context = rag_system.query(keyword, top_k=2)
                    if followup_context:
                        all_context.extend(followup_context)
                        gap_findings.append(f"✓ Follow-up query '{keyword}': {len(followup_context)} results")
                except Exception as e:
                    gap_findings.append(f"✗ Follow-up query '{keyword}' failed: {str(e)}")

            chain.add_step(
                "Identifying gaps and performing follow-up queries",
                gap_findings,
                f"Total context expanded to {len(all_context)} passages"
            )
        else:
            chain.add_step(
                "Checking for gaps",
                ["No specific follow-up topics identified"],
                "Initial context appears sufficient"
            )

        # Step 3: Deduplication
        seen_texts = set()
        unique_context = []
        duplicates = 0

        for text, metadata, score in all_context:
            text_normalized = text.strip().lower()[:200]  # First 200 chars for comparison
            if text_normalized not in seen_texts:
                seen_texts.add(text_normalized)
                unique_context.append((text, metadata, score))
            else:
                duplicates += 1

        dedup_findings = [
            f"Total passages retrieved: {len(all_context)}",
            f"Duplicates removed: {duplicates}",
            f"Unique passages: {len(unique_context)}"
        ]

        chain.add_step(
            "Deduplicating context",
            dedup_findings,
            f"Final context: {len(unique_context)} unique passages"
        )

        chain.set_conclusion(
            f"Multi-step analysis complete with {len(unique_context)} unique policy references",
            "HIGH"
        )

        return chain, unique_context


if __name__ == "__main__":
    # Example usage
    print("=== Chain of Thought Example ===\n")

    # Example 1: Classification reasoning
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

    # Example 2: Risk assessment
    print("\n" + "="*60 + "\n")

    detections = [
        {'type': 'SSN', 'value': '123-45-6789'},
        {'type': 'EMAIL', 'value': 'test@test.com'},
        {'type': 'PHONE_NUMBER', 'value': '555-1234'}
    ]

    risk_chain = RiskAssessmentReasoning.assess_risk(
        detections,
        critical_types={'SSN', 'MEDICAL_RECORD_NUMBER'},
        high_risk_types={'CREDIT_CARD', 'BANK_ACCOUNT'},
        medium_risk_types={'EMAIL', 'PHONE_NUMBER', 'PERSON_NAME'}
    )
    print(risk_chain.format())
