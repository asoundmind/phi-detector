"""
ChatBot for Canadian Privacy Compliance - combines PHI detection, RAG, and LLM.
"""

import re
import logging
from typing import Dict, Optional, List

from .phi_detector import PHIDetector
from .rag_system import RAGSystem
from .ollama_client import OllamaClient
from .prompt_templates import (
    SYSTEM_PROMPT,
    COT_SYSTEM_PROMPT,
    build_detection_prompt,
    build_policy_question_prompt,
    build_complete_prompt,
    build_cot_detection_prompt,
    build_cot_policy_question_prompt,
    build_cot_dev_ticket_prompt
)
from .chain_of_thought import (
    ReasoningChain,
    ClassificationReasoning,
    RiskAssessmentReasoning,
    ComplianceReasoning
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ChatBot:
    """
    Canadian Privacy Compliance ChatBot.

    Combines PHI detection, RAG-based policy retrieval, and LLM generation
    to provide privacy compliance assistance.
    """

    def __init__(
        self,
        model: str = "gemma2:2b",
        ollama_base_url: str = "http://localhost:11434",
        rag_collection: str = "privacy_policies",
        rag_persist_dir: str = "./chroma_db"
    ):
        """
        Initialize the ChatBot with all required components.

        Args:
            model: Ollama model to use
            ollama_base_url: Base URL for Ollama API
            rag_collection: ChromaDB collection name
            rag_persist_dir: Directory for ChromaDB persistence
        """
        try:
            logger.info("Initializing ChatBot...")

            # Initialize PHI Detector
            logger.info("Loading PHI Detector...")
            self.phi_detector = PHIDetector()

            # Initialize RAG System
            logger.info("Loading RAG System...")
            self.rag = RAGSystem(
                collection_name=rag_collection,
                persist_directory=rag_persist_dir
            )

            # Initialize Ollama Client
            logger.info("Loading Ollama Client...")
            self.llm = OllamaClient(
                model=model,
                base_url=ollama_base_url
            )

            # Verify Ollama is running
            if not self.llm.check_health():
                logger.warning(
                    "Ollama health check failed. The chatbot will work for detection "
                    "but LLM-enhanced responses will not be available."
                )

            logger.info("ChatBot initialized successfully!")

        except Exception as e:
            logger.error(f"Failed to initialize ChatBot: {e}")
            raise

    def _classify_message(self, message: str, return_reasoning: bool = False):
        """
        Classify message into one of three types with optional reasoning chain.
        - 'pii_ticket': Support ticket with actual PII to detect
        - 'dev_ticket': Development/PM ticket about requirements and compliance
        - 'question': General policy question

        Args:
            message: Input message text
            return_reasoning: If True, return tuple of (classification, reasoning_chain)

        Returns:
            Message type: 'pii_ticket', 'dev_ticket', or 'question'
            Or tuple if return_reasoning is True
        """
        try:
            if not message or not message.strip():
                if return_reasoning:
                    chain = ReasoningChain("Message Classification")
                    chain.add_step("Input validation", ["Message is empty"], "Default to question")
                    chain.set_conclusion("question", "HIGH")
                    return 'question', chain
                return 'question'

            message_lower = message.lower()

            # Check for actual PII patterns (real user data)
            has_email = bool(re.search(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', message))
            has_phone = bool(re.search(r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b', message))
            has_ssn = bool(re.search(r'\b\d{3}-\d{2,3}-\d{3,4}\b', message))
            has_account = bool(re.search(r'\b(?:account|acct|patient)\s*#?\s*:?\s*[A-Z0-9]{5,}\b', message, re.IGNORECASE))
            has_dob = bool(re.search(r'\b(?:dob|date of birth|born)[\s:]+\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b', message_lower))

            patterns = {
                'Email': has_email,
                'Phone': has_phone,
                'SSN': has_ssn,
                'Account Number': has_account,
                'Date of Birth': has_dob
            }

            phi_count = sum(patterns.values())

            # Create PII pattern analysis reasoning
            pii_chain = ClassificationReasoning.analyze_pii_patterns(message, patterns)

            # If has 2+ actual PII items, it's a support ticket with PII
            if phi_count >= 2:
                logger.info("Classified as: PII Support Ticket")
                if return_reasoning:
                    pii_chain.set_conclusion("PII Support Ticket", "HIGH")
                    return 'pii_ticket', pii_chain
                return 'pii_ticket'

            # Check for development/PM ticket indicators
            dev_keywords = [
                'pm ', 'product manager', 'project manager',
                'developing', 'building', 'creating', 'implementing',
                'feature', 'functionality', 'system', 'application',
                'storing', 'store', 'database', 'save',
                'encryption', 'encrypt', 'security measure',
                'technology', 'technical', 'architecture',
                'requirement', 'compliance', 'regulation',
                'chat message', 'messaging system', 'communication',
                'between user', 'between patient', 'between client'
            ]

            found_indicators = [ind for ind in dev_keywords if ind in message_lower]
            has_dev_indicators = len(found_indicators)

            # Check for question words (common in dev tickets)
            question_words = ['should', 'need', 'require', 'must', 'recommend', 'what', 'how']
            has_questions = any(qw in message_lower for qw in question_words)

            # Create dev ticket analysis reasoning
            dev_chain = ClassificationReasoning.analyze_dev_indicators(message, found_indicators, has_questions)

            # If it has dev indicators AND questions, it's a dev ticket
            if has_dev_indicators >= 2 and has_questions:
                logger.info("Classified as: Development/Requirements Ticket")
                if return_reasoning:
                    # Combine both chains
                    combined_chain = ReasoningChain("Complete Message Classification")
                    combined_chain.steps.extend(pii_chain.steps)
                    combined_chain.steps.extend(dev_chain.steps)
                    combined_chain.set_conclusion("Development/Requirements Ticket", "HIGH")
                    return 'dev_ticket', combined_chain
                return 'dev_ticket'

            # Default to general question
            logger.info("Classified as: General Policy Question")
            if return_reasoning:
                combined_chain = ReasoningChain("Complete Message Classification")
                combined_chain.steps.extend(pii_chain.steps)
                if found_indicators or has_questions:
                    combined_chain.steps.extend(dev_chain.steps)
                combined_chain.set_conclusion("General Policy Question", "HIGH")
                return 'question', combined_chain
            return 'question'

        except Exception as e:
            logger.error(f"Error in _classify_message: {e}")
            if return_reasoning:
                chain = ReasoningChain("Message Classification (Error)")
                chain.add_step("Error occurred", [str(e)], "Default to question")
                chain.set_conclusion("question", "LOW")
                return 'question', chain
            return 'question'

    def answer_dev_ticket(self, ticket_text: str, top_k: int = 3, return_prompt: bool = False, use_cot: bool = True):
        """
        Answer a development/PM ticket about technical requirements and compliance.

        Args:
            ticket_text: Development ticket text
            top_k: Number of context chunks to retrieve
            return_prompt: If True, return tuple with prompt and metadata
            use_cot: If True, use chain of thought prompting and multi-step RAG

        Returns:
            LLM-generated answer with policy guidance and technical recommendations
        """
        try:
            logger.info("Processing development ticket...")

            # Query RAG system for relevant compliance context
            logger.info("Retrieving relevant policy context...")
            context_chunks = self.rag.query(ticket_text, top_k=top_k)

            if not context_chunks:
                msg = (
                    "I don't have enough policy information to provide guidance. "
                    "Please ensure policy documents have been loaded into the system."
                )
                if return_prompt:
                    return msg, "", [], None
                return msg

            logger.info(f"Retrieved {len(context_chunks)} relevant chunks")

            # Use multi-step RAG analysis if CoT is enabled
            rag_reasoning = None
            if use_cot:
                try:
                    logger.info("Performing multi-step RAG analysis...")
                    rag_reasoning, context_chunks = ComplianceReasoning.multi_step_analysis(
                        ticket_text,
                        context_chunks,
                        self.rag
                    )
                    logger.info(f"Multi-step analysis complete: {len(context_chunks)} unique passages")
                except Exception as e:
                    logger.warning(f"Multi-step RAG failed, using initial context: {e}")

            # Build prompt - use CoT prompt if enabled
            if use_cot:
                full_prompt = build_cot_dev_ticket_prompt(ticket_text, context_chunks)
            else:
                # Original prompt format
                context_text = "\n\n".join([
                    f"[Source: {metadata.get('source', 'Unknown').split('/')[-1]}]\n{text}"
                    for text, metadata, score in context_chunks
                ])

                full_prompt = f"""You are a privacy compliance advisor helping development teams.

DEVELOPMENT TICKET:
{ticket_text}

RELEVANT PRIVACY REGULATIONS AND POLICIES:
{context_text}

Please provide:
1. **Compliance Requirements**: What privacy regulations apply?
2. **Required Security Measures**: What technical safeguards are required (encryption, access controls, etc.)?
3. **Technology Recommendations**: Specific technologies or approaches recommended for compliance
4. **Risk Assessment**: What privacy risks need to be addressed?
5. **Best Practices**: Additional recommendations for implementation

Be specific and actionable in your recommendations."""

            # Generate response with LLM
            logger.info("Generating LLM response...")
            response = self.llm.generate(
                prompt=full_prompt,
                max_tokens=800 if use_cot else 600,  # More tokens for CoT responses
                temperature=0.4
            )

            if response:
                if return_prompt:
                    return response, full_prompt, context_chunks, rag_reasoning
                return response
            else:
                # Fallback
                logger.warning("LLM generation failed, returning context directly")
                fallback = self._format_basic_answer(ticket_text, context_chunks)
                if return_prompt:
                    return fallback, full_prompt, context_chunks, rag_reasoning
                return fallback

        except ValueError as e:
            logger.error(f"RAG error: {e}")
            error_msg = (
                "The policy knowledge base is not yet loaded. "
                "Please load policy documents before processing development tickets."
            )
            if return_prompt:
                return error_msg, "", [], None
            return error_msg

        except Exception as e:
            logger.error(f"Error processing development ticket: {e}")
            error_msg = f"Error processing development ticket: {str(e)}"
            if return_prompt:
                return error_msg, "", [], None
            return error_msg

    def _is_ticket(self, message: str) -> bool:
        """
        Determine if a message looks like a support ticket (backward compatibility).
        Now uses the new classification system internally.

        Args:
            message: Input message text

        Returns:
            True if message is any type of ticket, False if it's a question
        """
        msg_type = self._classify_message(message)
        return msg_type in ['pii_ticket', 'dev_ticket']

    def _assess_risk_level(self, detections: List[Dict], return_reasoning: bool = False):
        """
        Assess overall risk level based on detected PHI types with optional reasoning.

        Args:
            detections: List of PHI detections
            return_reasoning: If True, return tuple of (risk_level, reasoning_chain)

        Returns:
            Risk level: LOW, MEDIUM, HIGH, or CRITICAL
            Or tuple if return_reasoning is True
        """
        # Critical-risk PHI types (highest sensitivity)
        critical_types = {
            'SSN', 'Social Insurance Number (SIN)', 'MEDICAL_RECORD_NUMBER',
            'HEALTH_PLAN_NUMBER', 'Personal Health Number (PHN)',
            'DIAGNOSIS_CODE', 'PRESCRIPTION', 'Credit Card Number'
        }

        high_risk_types = {
            'CREDIT_CARD', 'BANK_ACCOUNT', 'DATE_OF_BIRTH',
            'BIOMETRIC', 'FULL_FACE_PHOTO'
        }

        medium_risk_types = {
            'PERSON_NAME', 'NAME', 'Phone Number', 'PHONE_NUMBER', 'Email Address', 'EMAIL',
            'IP Address', 'IP_ADDRESS', 'VEHICLE_ID', 'Postal Code'
        }

        # Use CoT reasoning for risk assessment
        risk_chain = RiskAssessmentReasoning.assess_risk(
            detections,
            critical_types,
            high_risk_types,
            medium_risk_types
        )

        # Extract the risk level from the conclusion
        if not detections:
            risk_level = "LOW"
        else:
            detected_types = {d['type'] for d in detections}

            # Check for critical PHI
            if detected_types & critical_types:
                risk_level = "CRITICAL"
            # Check for high-risk PHI
            elif detected_types & high_risk_types:
                risk_level = "HIGH"
            # Check for medium-risk PHI
            elif detected_types & medium_risk_types:
                # If many medium-risk items, escalate to HIGH
                if len(detections) > 5:
                    risk_level = "HIGH"
                else:
                    risk_level = "MEDIUM"
            else:
                # Default to LOW
                risk_level = "LOW"

        if return_reasoning:
            return risk_level, risk_chain
        return risk_level

    def _build_detection_prompt(
        self,
        ticket: str,
        detections: List[Dict],
        risk: str
    ) -> str:
        """
        Build a detection analysis prompt using the DETECTION_PROMPT template.

        Args:
            ticket: Support ticket text
            detections: List of PHI detections
            risk: Risk level (LOW, MEDIUM, HIGH, CRITICAL)

        Returns:
            Formatted prompt for LLM
        """
        try:
            # Use the imported prompt builder
            user_prompt = build_detection_prompt(
                ticket_text=ticket,
                detections=detections,
                risk_level=risk
            )

            # Combine with system prompt
            full_prompt = build_complete_prompt(SYSTEM_PROMPT, user_prompt)

            return full_prompt

        except Exception as e:
            logger.error(f"Error building detection prompt: {e}")
            raise

    def _build_policy_prompt(self, question: str, rag_results: List) -> str:
        """
        Build a policy question prompt using the POLICY_QUESTION_PROMPT template.

        Args:
            question: User's question about privacy policies
            rag_results: Retrieved context chunks from RAG system (list of tuples)

        Returns:
            Formatted prompt for LLM
        """
        try:
            # Use the imported prompt builder
            user_prompt = build_policy_question_prompt(
                question=question,
                context_chunks=rag_results
            )

            # Combine with system prompt
            full_prompt = build_complete_prompt(SYSTEM_PROMPT, user_prompt)

            return full_prompt

        except Exception as e:
            logger.error(f"Error building policy prompt: {e}")
            raise

    def analyze_ticket(self, text: str, return_prompt: bool = False, use_cot: bool = True):
        """
        Analyze a support ticket for PHI and privacy risks using RAG-grounded responses.

        Args:
            text: Support ticket text
            return_prompt: If True, return tuple of (response, prompt, detections, risk_level, context_chunks, reasoning)
            use_cot: If True, use chain of thought prompting and reasoning

        Returns:
            LLM-generated analysis of the ticket with risk assessment based on policy documents
            Or tuple if return_prompt is True
        """
        try:
            logger.info("Analyzing ticket for PHI...")

            # Detect PHI using analyze() method
            result = self.phi_detector.analyze(text)
            detections = result.get('detections', [])
            logger.info(f"Found {len(detections)} PHI detections")

            # Assess risk level with reasoning
            if use_cot:
                risk_level, risk_reasoning = self._assess_risk_level(detections, return_reasoning=True)
            else:
                risk_level = self._assess_risk_level(detections)
                risk_reasoning = None
            logger.info(f"Risk level: {risk_level}")

            # Build RAG query based on detected PII types and risk level
            detected_types = set(d['type'] for d in detections)
            rag_query = f"How should we handle and protect {', '.join(detected_types)} information? What are the security requirements and privacy obligations for {risk_level} risk personal information?"

            # Retrieve relevant policy context using RAG
            logger.info("Retrieving relevant policy guidance from knowledge base...")
            try:
                context_chunks = self.rag.query(rag_query, top_k=3)
            except Exception as rag_error:
                logger.warning(f"RAG query failed: {rag_error}, continuing without policy context")
                context_chunks = []

            # Build enhanced prompt with policy context
            if context_chunks:
                if use_cot:
                    # Use CoT prompt with RAG context
                    full_prompt = build_cot_detection_prompt(text, detections, risk_level, context_chunks)
                else:
                    # Original prompt format
                    context_text = "\n\n".join([
                        f"[Policy Source: {metadata.get('source', 'Unknown').split('/')[-1]}]\n{text}"
                        for text, metadata, score in context_chunks
                    ])

                    full_prompt = f"""You are a privacy compliance advisor. Analyze this support ticket for PII and provide guidance based on Canadian privacy regulations.

SUPPORT TICKET:
{text}

DETECTED PII:
{self._format_detections_for_prompt(detections)}

RISK LEVEL: {risk_level}

RELEVANT PRIVACY REGULATIONS:
{context_text}

Based on the detected PII and the privacy regulations above, provide:
1. **Summary of Detected PII**: List what was found
2. **Risk Assessment**: Explain the privacy risks
3. **Handling Requirements**: What regulations apply and what's required
4. **Recommended Actions**: Specific steps to protect this information
5. **Compliance Notes**: Any additional compliance considerations

Be specific and cite the relevant regulations."""
            else:
                # Fallback if RAG fails
                if use_cot:
                    full_prompt = build_cot_detection_prompt(text, detections, risk_level, context_chunks)
                else:
                    full_prompt = self._build_detection_prompt(
                        ticket=text,
                        detections=detections,
                        risk=risk_level
                    )

            # Generate response with LLM
            logger.info("Generating LLM response...")
            response = self.llm.generate(
                prompt=full_prompt,
                max_tokens=800 if use_cot else 600,  # More tokens for CoT responses
                temperature=0.3  # Lower temperature for more consistent analysis
            )

            if response:
                if return_prompt:
                    return response, full_prompt, detections, risk_level, context_chunks, risk_reasoning
                return response
            else:
                # Fallback if LLM fails
                logger.warning("LLM generation failed, returning basic analysis")
                fallback = self._format_basic_detection(detections, risk_level)
                if return_prompt:
                    return fallback, full_prompt, detections, risk_level, context_chunks, risk_reasoning
                return fallback

        except Exception as e:
            logger.error(f"Error analyzing ticket: {e}")
            error_msg = f"Error analyzing ticket: {str(e)}"
            if return_prompt:
                return error_msg, "", [], "LOW", [], None
            return error_msg

    def _format_detections_for_prompt(self, detections: List[Dict]) -> str:
        """Format detections for inclusion in prompt."""
        if not detections:
            return "No PII detected"

        lines = []
        for det in detections:
            lines.append(f"- {det['type']}: {det['value']}")
        return "\n".join(lines)

    def answer_question(self, question: str, top_k: int = 2, return_prompt: bool = False, use_cot: bool = True):
        """
        Answer a privacy policy question using RAG and LLM.

        Args:
            question: User's question about privacy policies
            top_k: Number of context chunks to retrieve
            return_prompt: If True, return tuple of (response, prompt, context_chunks)
            use_cot: If True, use chain of thought prompting

        Returns:
            LLM-generated answer with citations
            Or tuple if return_prompt is True
        """
        try:
            logger.info(f"Answering question: {question}")

            # Query RAG system for relevant context
            logger.info("Retrieving relevant policy context...")
            context_chunks = self.rag.query(question, top_k=top_k)

            if not context_chunks:
                msg = (
                    "I don't have enough policy information to answer that question. "
                    "Please ensure policy documents have been loaded into the system."
                )
                if return_prompt:
                    return msg, "", []
                return msg

            logger.info(f"Retrieved {len(context_chunks)} relevant chunks")

            # Build policy question prompt - use CoT if enabled
            if use_cot:
                full_prompt = build_cot_policy_question_prompt(question, context_chunks)
            else:
                full_prompt = self._build_policy_prompt(
                    question=question,
                    rag_results=context_chunks
                )

            # Generate response with LLM
            logger.info("Generating LLM response...")
            response = self.llm.generate(
                prompt=full_prompt,
                max_tokens=600 if use_cot else 400,  # More tokens for CoT
                temperature=0.4  # Slightly higher for more natural language
            )

            if response:
                if return_prompt:
                    return response, full_prompt, context_chunks
                return response
            else:
                # Fallback if LLM fails
                logger.warning("LLM generation failed, returning context directly")
                fallback = self._format_basic_answer(question, context_chunks)
                if return_prompt:
                    return fallback, full_prompt, context_chunks
                return fallback

        except ValueError as e:
            # Handle empty collection
            logger.error(f"RAG error: {e}")
            error_msg = (
                "The policy knowledge base is not yet loaded. "
                "Please load policy documents before asking questions."
            )
            if return_prompt:
                return error_msg, "", []
            return error_msg

        except Exception as e:
            logger.error(f"Error answering question: {e}")
            error_msg = f"Error processing question: {str(e)}"
            if return_prompt:
                return error_msg, "", []
            return error_msg

    def chat(self, message: str, return_prompt: bool = False, use_cot: bool = True):
        """
        Main chat interface - routes messages to appropriate handler with CoT support.

        Args:
            message: User's input message
            return_prompt: If True, return tuple with prompt and metadata
            use_cot: If True, use chain of thought reasoning and prompting

        Returns:
            ChatBot response (PII ticket, dev ticket, or question answer)
            Or tuple if return_prompt is True: (response, prompt, metadata, message_type)
        """
        try:
            if not message or not message.strip():
                msg = "Please provide a message or question."
                if return_prompt:
                    return msg, "", {}, 'question'
                return msg

            logger.info(f"Processing message (length: {len(message)} chars)")

            # Classify message type with reasoning if CoT enabled
            if use_cot and return_prompt:
                msg_type, classification_reasoning = self._classify_message(message, return_reasoning=True)
            else:
                msg_type = self._classify_message(message)
                classification_reasoning = None
            logger.info(f"Message classified as: {msg_type}")

            if msg_type == 'pii_ticket':
                # Support ticket with actual PII
                logger.info("Processing as PII support ticket")
                if return_prompt:
                    response, prompt, detections, risk_level, context_chunks, risk_reasoning = self.analyze_ticket(
                        message, return_prompt=True, use_cot=use_cot
                    )
                    metadata = {
                        'detections': detections,
                        'risk_level': risk_level,
                        'context_chunks': context_chunks,
                        'classification_reasoning': classification_reasoning,
                        'risk_reasoning': risk_reasoning
                    }
                    return response, prompt, metadata, 'pii_ticket'
                else:
                    return self.analyze_ticket(message, use_cot=use_cot)

            elif msg_type == 'dev_ticket':
                # Development/PM ticket about requirements
                logger.info("Processing as development/requirements ticket")
                if return_prompt:
                    response, prompt, context_chunks, rag_reasoning = self.answer_dev_ticket(
                        message, return_prompt=True, use_cot=use_cot
                    )
                    metadata = {
                        'context_chunks': context_chunks,
                        'ticket_type': 'development',
                        'classification_reasoning': classification_reasoning,
                        'rag_reasoning': rag_reasoning
                    }
                    return response, prompt, metadata, 'dev_ticket'
                else:
                    return self.answer_dev_ticket(message, use_cot=use_cot)

            else:
                # General policy question
                logger.info("Processing as policy question")
                if return_prompt:
                    response, prompt, context_chunks = self.answer_question(
                        message, return_prompt=True, use_cot=use_cot
                    )
                    metadata = {
                        'context_chunks': context_chunks,
                        'classification_reasoning': classification_reasoning
                    }
                    return response, prompt, metadata, 'question'
                else:
                    return self.answer_question(message, use_cot=use_cot)

        except Exception as e:
            logger.error(f"Error in chat: {e}")
            error_msg = f"An error occurred: {str(e)}"
            if return_prompt:
                return error_msg, "", {}, 'question'
            return error_msg

    def _format_basic_detection(self, detections: List[Dict], risk_level: str) -> str:
        """
        Fallback formatter for detections when LLM is unavailable.

        Args:
            detections: List of PHI detections
            risk_level: Overall risk level

        Returns:
            Formatted detection report
        """
        if not detections:
            return "No personal information detected. ✅"

        risk_indicators = {
            "LOW": "🟢",
            "MEDIUM": "🟡",
            "HIGH": "🟠",
            "CRITICAL": "🔴"
        }

        indicator = risk_indicators.get(risk_level, "⚪")

        output = [
            f"\n{indicator} **Risk Level: {risk_level}**\n",
            "**Detected Personal Information:**\n"
        ]

        # Group by type
        by_type = {}
        for det in detections:
            det_type = det['type']
            if det_type not in by_type:
                by_type[det_type] = []
            by_type[det_type].append(det['value'])

        for det_type, values in by_type.items():
            output.append(f"- {det_type}: {len(values)} occurrence(s)")

        output.append("\n**Recommendation:** Review and handle this information according to privacy policies.")

        return "\n".join(output)

    def _format_basic_answer(self, question: str, context_chunks: List) -> str:
        """
        Fallback formatter for answers when LLM is unavailable.

        Args:
            question: Original question
            context_chunks: Retrieved context

        Returns:
            Formatted answer with context
        """
        output = [
            f"**Question:** {question}\n",
            "**Relevant Policy Information:**\n"
        ]

        for i, (text, metadata, score) in enumerate(context_chunks, 1):
            source = metadata.get('source', 'Unknown')
            source_name = source.split('/')[-1] if '/' in source else source

            output.append(f"\n**[{i}] From {source_name}:**")
            output.append(text.strip())

        return "\n".join(output)


if __name__ == "__main__":
    # Example usage
    try:
        # Initialize chatbot
        print("Initializing ChatBot...")
        chatbot = ChatBot()

        # Example ticket
        print("\n" + "="*80)
        print("EXAMPLE 1: Ticket Analysis")
        print("="*80)

        ticket = """Ticket #12345
Customer John Doe called regarding account access.
Phone: 604-555-0123
Email: john.doe@example.com
Date of Birth: 01/15/1985

Issue: Unable to access medical records online."""

        response = chatbot.chat(ticket)
        print(response)

        # Example question
        print("\n" + "="*80)
        print("EXAMPLE 2: Policy Question")
        print("="*80)

        question = "What are the consent requirements for collecting personal information?"
        response = chatbot.chat(question)
        print(response)

    except Exception as e:
        logger.error(f"Error in main: {e}")
